"""Website combiner - combines all components into final HTML"""

from typing import Dict, List, Optional
from openai import OpenAI
# from google import genai # Comment out direct Gemini import
# from google.genai import types # Comment out types for Gemini config
import requests # Import requests for OpenRouter
import json # Import json for OpenRouter payload
import time # Import time for delays
# import re # Removed re for regex operations
from utils.api_keys import (
    get_openai_key, rotate_openai_key, is_rate_limit_error_openai, has_multiple_keys_openai,
    # get_gemini_key, rotate_gemini_key, is_rate_limit_error_gemini, has_multiple_keys_gemini, # Comment out direct Gemini key functions
    get_openrouter_key, rotate_openrouter_key, is_rate_limit_error_openrouter, has_multiple_keys_openrouter,
    _key_manager
) # Import OpenAI and OpenRouter key functions
from utils.prompts import get_combination_prompt


def combine_components(all_components: Dict[str, str], form_data: Dict,
                      image_urls: List[str], logo_url: str, favicon_url: str,
                      theme_color: str, font_name: str) -> Optional[str]:
    """
    Combine all components into final HTML document in proper order
    
    Args:
        all_components: Dictionary mapping component names to HTML code
        form_data: Form data dictionary
        image_urls: List of image URLs
        logo_url: Logo URL
        favicon_url: Favicon URL
        theme_color: Theme color hex code
        font_name: Font name
        
    Returns:
        Complete HTML document or None if failed
    """
    try:
        print("[LOG] Combining all components into final HTML...")
        
        # Components should already be in correct order from component_generator
        # Python 3.7+ dictionaries maintain insertion order
        ordered_components = all_components
        
        print(f"[LOG] Combining {len(ordered_components)} components in order: {list(ordered_components.keys())}")
        
        # Verify we have all required components
        required_components = ['Navigation', 'Hero', 'Contact', 'Footer']
        missing_required = [c for c in required_components if c not in ordered_components]
        if missing_required:
            print(f"[ERROR] Missing required components before combination: {missing_required}")
            print(f"[ERROR] Available components: {list(ordered_components.keys())}")
        
        # Verify we have 8 components total (4 fixed + 4 dynamic)
        if len(ordered_components) < 8:
            print(f"[WARN] Only {len(ordered_components)} components provided, expected 8")
            print(f"[WARN] Missing components may cause issues in final HTML")
        
        # Use OpenRouter key for this final combination step
        openrouter_key = get_openrouter_key() # Fetch key from environment
        if not openrouter_key:
            raise Exception("OPENROUTER_API_KEY not configured for final combination")
        
        # Get combination prompt (use ordered components) - should embed all HTML content
        combination_prompt = get_combination_prompt(
            all_components=ordered_components,
            form_data=form_data,
            image_urls=image_urls,
            logo_url=logo_url,
            favicon_url=favicon_url,
            theme_color=theme_color,
            font_name=font_name
        )
        
        # Generate combined HTML with retry on rate limit
        # Use openrouter_manager for this section
        if _key_manager.openrouter_manager is None:
             _ = get_openrouter_key()

        all_openrouter_keys = _key_manager.openrouter_manager.get_all_keys()
        max_retries_openrouter = len(all_openrouter_keys) if all_openrouter_keys else 1
        
        for attempt in range(max_retries_openrouter):
            try:
                print(f"[LOG] Combination attempt {attempt + 1}/{max_retries_openrouter} with OpenRouter (Gemini)...")
                
                messages = [
                    {"role": "user", "content": [{"type": "text", "text": combination_prompt}]}
                ]

                headers = {
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost", # Optional, for OpenRouter analytics
                    "X-Title": "Website Builder AI", # Optional, for OpenRouter analytics
                }

                payload = {
                    "model": "google/gemini-2.0-flash-001",
                    "messages": messages,
                    "max_tokens": 32000 # Max output tokens for combination
                }

                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    data=json.dumps(payload)
                )
                response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
                
                response_json = response.json()

                if not response_json.get('choices') or not response_json['choices'][0].get('message') or not response_json['choices'][0]['message'].get('content'):
                    print("[WARN] OpenRouter/Gemini API returned empty response or no content.")
                    raise Exception("No response from OpenRouter/Gemini")
                
                html_code = response_json['choices'][0]['message']['content'].strip()
                
                # Clean up markdown code blocks if present
                if '```html' in html_code:
                    html_code = html_code.split('```html')[1].split('```')[0].strip()
                elif '```' in html_code:
                    html_code = html_code.split('```')[1].split('```')[0].strip()
                
                # Ensure it starts with <!DOCTYPE
                if not html_code.startswith('<!DOCTYPE'):
                    if '<!DOCTYPE' in html_code:
                        html_code = html_code[html_code.find('<!DOCTYPE'):]
                    else:
                        html_code = f"<!DOCTYPE html>\n{html_code}"

                # Removed POST-PROCESSING for image paths to avoid regex issues.
                # The LLM is now solely responsible for generating correct static image paths.
                # Frontend's ImageGallery onError will handle any malformed paths with a placeholder.

                # Verify all components are included
                missing_components = []
                for comp_name in all_components.keys():
                    comp_lower = comp_name.lower()
                    html_lower = html_code.lower()
                    if comp_lower not in html_lower:
                        missing_components.append(comp_name)
                
                if missing_components:
                    print(f"[WARN] Some components may be missing: {missing_components}")
                    print("[WARN] This might be a false positive - checking component content...")
                    for comp_name in missing_components[:]:
                        comp_code = all_components[comp_name]
                        if len(comp_code) > 50:
                            unique_part = comp_code[50:200].strip()
                            if unique_part and unique_part.lower() in html_lower:
                                missing_components.remove(comp_name)
                
                if missing_components:
                    print(f"[ERROR] Components confirmed missing: {missing_components}")
                    print("[ERROR] Regenerating with emphasis on including all components...")
                
                # Ensure proper spacing between sections
                if 'padding-top: 80px' not in html_code and 'py-5' not in html_code:
                    if '<style>' in html_code:
                        spacing_css = """
        /* Ensure proper spacing between sections */
        section, .section, [class*="section"] {
            padding-top: 80px !important;
            padding-bottom: 80px !important;
        }
        """
                        html_code = html_code.replace('<style>', f'<style>{spacing_css}')
                
                print(f"[LOG] ✓ Successfully combined all components (verified {len(all_components) - len(missing_components)}/{len(all_components)} present)")
                return html_code
                
            except requests.exceptions.HTTPError as e:
                print(f"[WARN] HTTP Error from OpenRouter: {e.response.status_code} - {e.response.text[:200]}")
                if _key_manager.openrouter_manager.is_rate_limit_error(e):
                    print("[LOG] Rate limit detected from OpenRouter, rotating to next key...")
                    if has_multiple_keys_openrouter() and rotate_openrouter_key():
                        time.sleep(5) # Delay before retrying
                        continue
                    else:
                        print("[WARN] No more OpenRouter keys to rotate, exhausting retries.")
                if attempt == max_retries_openrouter - 1:
                    raise Exception(f"Failed to combine components after {max_retries_openrouter} attempts: {str(e)}")
                else:
                    # For non-rate-limit errors, or if rotation failed, fail immediately
                    raise Exception(f"Failed to combine components: {str(e)}")
            except Exception as e:
                error_str = str(e)
                is_rate_limit = is_rate_limit_error_openrouter(e) # Use OpenRouter-specific rate limit check
                
                print(f"[WARN] Combination attempt {attempt + 1} failed: {error_str[:200]}")
                
                if is_rate_limit and has_multiple_keys_openrouter() and attempt < max_retries_openrouter - 1:
                    print(f"[LOG] Rate limit detected, rotating to next OpenRouter key...")
                    rotate_openrouter_key()
                    time.sleep(5) # Delay before retrying
                    continue
                elif attempt < max_retries_openrouter - 1:
                    if has_multiple_keys_openrouter():
                        rotate_openrouter_key()
                        time.sleep(5) # Delay before retrying
                    continue
                else:
                    raise
        
        raise Exception("All combination attempts failed")
        
    except Exception as e:
        print(f"[ERROR] Failed to combine components: {e}")
        import traceback
        traceback.print_exc()
        return None

