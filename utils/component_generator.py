"""Component generation system for individual website components"""

from typing import Dict, List, Optional
from openai import OpenAI # Keep OpenAI for image generation
# from google import genai # Comment out direct Gemini import
# from google.genai import types # Comment out types for Gemini config
import base64
from PIL import Image
from io import BytesIO
import os
import requests # Import requests for OpenRouter
import json # Import json for OpenRouter payload
from utils.api_keys import (
    get_openai_key, rotate_openai_key, is_rate_limit_error_openai, has_multiple_keys_openai,
    # get_gemini_key, rotate_gemini_key, is_rate_limit_error_gemini, has_multiple_keys_gemini, # Comment out direct Gemini key functions
    get_openrouter_key, rotate_openrouter_key, is_rate_limit_error_openrouter, has_multiple_keys_openrouter,
    _key_manager
)
from utils.bootstrap_docs import get_or_upload_bootstrap_docs
from utils.prompts import get_component_prompt
import time # Import time for delays
import shutil # Import shutil for file copying


def generate_image_for_component(component_info: Dict, business_category: str,
                                 business_sub_category: str, theme_color: str,
                                 timestamp: str, openai_client: OpenAI) -> Optional[str]:
    """
    Generate an image for a component on-demand using OpenAI image API
    
    Args:
        component_info: Component dict with image_prompt, image_dimensions, etc.
        business_category: Business category
        business_sub_category: Business subcategory
        theme_color: Theme color
        timestamp: Timestamp for unique filename
        openai_client: OpenAI client instance
        
    Returns:
        Image URL (relative path) or None if failed
    """
    try:
        comp_name = component_info.get('name', 'component')
        image_prompt = component_info.get('image_prompt', '')
        
        if not image_prompt:
            print(f"[WARN] No image prompt for component {comp_name}, skipping image generation")
            return None
        
        # Fallback image paths
        hero_fallback_path = "/static/generated/hero_20251105_142354_0.png"
        additional_fallback_path = "/static/generated/additional_20251106_160031_2.png"

        print(f"[LOG] Generating image for component: {comp_name}")
        print(f"[LOG] Image prompt: {image_prompt[:100]}...")
        
        # Ensure static/generated directory exists
        os.makedirs('static/generated', exist_ok=True)
        
        # Try to generate image with retry on rate limit
        # Use _key_manager for OpenAI images
        if _key_manager.openai_manager is None:
             _ = get_openai_key()

        all_openai_keys = _key_manager.openai_manager.get_all_keys()
        max_retries = len(all_openai_keys) if all_openai_keys else 1
        
        for attempt in range(max_retries):
            try:
                print(f"[LOG] Image generation attempt {attempt + 1}/{max_retries} for {comp_name}...")
                
                # Use the provided openai_client which is already configured
                print(f"[LOG] Image generation for {comp_name} - DALL-E prompt: {image_prompt[:100]}...")
                
                img_response = openai_client.images.generate(
                    model="dall-e-3",
                    prompt=image_prompt,
                    n=1,
                    size="1024x1024"
                )

                if img_response.data and img_response.data[0].url:
                    dalle_url = img_response.data[0].url
                    print(f"[LOG] DALL-E generated URL for {comp_name}: {dalle_url}")
                    
                    # Download and save image locally
                    response = requests.get(dalle_url, stream=True)
                    response.raise_for_status()
                    
                    # Create filename based on component name
                    comp_slug = comp_name.lower().replace(' ', '_').replace('-', '_')
                    filename = f"{comp_slug}_{timestamp}.png"
                    image_path = os.path.join('static/generated', filename)
                    
                    with open(image_path, 'wb') as out_file:
                        shutil.copyfileobj(response.raw, out_file)
                    
                    local_image_url = f"/static/generated/{filename}"
                    print(f"[LOG] ✓ Image downloaded and saved locally for {comp_name}: {local_image_url}")
                    return local_image_url
                
                print(f"[WARN] No image data in response for {comp_name}")
                
            except Exception as e:
                error_str = str(e)
                is_rate_limit = is_rate_limit_error_openai(e)
                
                print(f"[WARN] Image generation attempt {attempt + 1} failed for {comp_name}: {error_str[:200]}")
                
                if is_rate_limit and has_multiple_keys_openai() and attempt < max_retries - 1:
                    print(f"[LOG] Rate limit detected, rotating to next key...")
                    rotate_openai_key()
                    openai_client = OpenAI(api_key=get_openai_key())
                    time.sleep(5) # Add delay after rotation
                    continue
                elif has_multiple_keys_openai() and attempt < max_retries - 1:
                    rotate_openai_key()
                    openai_client = OpenAI(api_key=get_openai_key())
                    time.sleep(5) # Add delay after rotation
                    continue
                else:
                    break
        
        print(f"[ERROR] Failed to generate image for {comp_name} after {max_retries} attempts")
        
        # FALLBACK: Return a local image path if all attempts fail
        if comp_name == "Hero":
            print(f"[WARN] Falling back to default Hero image: {hero_fallback_path}")
            return hero_fallback_path
        else:
            print(f"[WARN] Falling back to default additional image: {additional_fallback_path}")
            return additional_fallback_path
        
    except Exception as e:
        print(f"[ERROR] Error in generate_image_for_component for {comp_name}: {e}")
        import traceback
        traceback.print_exc()
        
        # Secondary fallback in case of unexpected errors
        if comp_name == "Hero":
            return hero_fallback_path
        else:
            return additional_fallback_path


def _is_permission_error(error: Exception) -> bool:
    error_text = str(error).lower()
    if 'permission' in error_text or 'permission_denied' in error_text:
        return True
    if '403' in error_text:
        return True
    # Check nested args if available
    if hasattr(error, 'args'):
        for arg in error.args:
            if isinstance(arg, dict):
                if str(arg).lower().find('permission') != -1 or str(arg).lower().find('403') != -1:
                    return True
            else:
                arg_text = str(arg).lower()
                if 'permission' in arg_text or '403' in arg_text:
                    return True
    return False


async def generate_component(component_name: str, component_purpose: str, form_data: Dict,
                           image_urls: List[str],
                           theme_color: str, font_name: str, business_category: str, business_sub_category: str,
                           openrouter_key: str, # Add openrouter_key as a direct argument
                           logo_url: Optional[str] = None, favicon_url: Optional[str] = None,
                           bootstrap_files: Optional[Dict[str, str]] = None,
                           component_design_info: Optional[Dict] = None,
                           image_prompts_info: Optional[Dict] = None) -> Optional[str]:
    """
    Generate a single component using LLM with retry, key rotation, and Bootstrap doc refresh
    """
    print(f"[LOG] Generating component: {component_name}...")
    print(f"[DEBUG] openrouter_key received in generate_component: {openrouter_key[:5]}...{openrouter_key[-5:]}") # Debugging key

    # Get component prompt once (independent of retries)
    component_prompt = get_component_prompt(
        component_name=component_name,
        component_purpose=component_purpose,
        form_data=form_data,
        image_urls=image_urls,
        logo_url=logo_url,
        favicon_url=favicon_url, # Pass favicon_url
        theme_color=theme_color,
        font_name=font_name,
        business_category=business_category,
        business_sub_category=business_sub_category,
        component_design_info=component_design_info,
        image_prompts_info=image_prompts_info
    )

    def build_contents(include_bootstrap: bool) -> List[str]:
        contents_list: List[str] = [component_prompt]
        if include_bootstrap and bootstrap_files:
            for file_uri, mime_type in bootstrap_files:
                try:
                    with open(file_uri.replace('file://', ''), 'r') as f:
                        bootstrap_content = f.read()
                    contents_list.append(f"Bootstrap documentation ({os.path.basename(file_uri)}):\n{bootstrap_content}")
                except Exception as e:
                    print(f"[WARN] Could not read bootstrap file {file_uri}: {e}")
        return contents_list

    # Retry with key rotation
    if _key_manager.openrouter_manager is None:
        # _ = get_openrouter_key()
        pass # No need to re-initialize if key is passed directly

    all_openrouter_keys = _key_manager.openrouter_manager.get_all_keys()
    max_retries = len(all_openrouter_keys) if all_openrouter_keys else 1

    use_bootstrap_docs = True if bootstrap_files else False
    last_error: Optional[Exception] = None
    retry_delay = 5 # seconds

    for attempt in range(max_retries):
        try:
            print(f"[LOG] Component generation attempt {attempt + 1}/{max_retries} for {component_name} with OpenRouter (Gemini)...")
            
            messages = [
                {"role": "user", "content": [{"type": "text", "text": item}]} for item in build_contents(include_bootstrap=use_bootstrap_docs)
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
                "max_tokens": 16000 # Max output tokens for component generation
            }

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload)
            )
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            
            response_json = response.json()

            if not response_json.get('choices') or not response_json['choices'][0].get('message') or not response_json['choices'][0]['message'].get('content'):
                print(f"[WARN] No response for component {component_name} from OpenRouter/Gemini")
                last_error = Exception("Empty response from OpenRouter/Gemini")
                continue

            component_code = response_json['choices'][0]['message']['content'].strip()

            if '```html' in component_code:
                component_code = component_code.split('```html')[1].split('```')[0].strip()
            elif '```' in component_code:
                component_code = component_code.split('```')[1].split('```')[0].strip()

            print(f"[LOG] ✓ Successfully generated component: {component_name}")
            return component_code

        except requests.exceptions.HTTPError as e:
            last_error = e
            print(f"[WARN] HTTP Error from OpenRouter: {e.response.status_code} - {e.response.text[:200]}")
            if _key_manager.openrouter_manager.is_rate_limit_error(e):
                print("[LOG] Rate limit detected from OpenRouter, rotating to next key...")
                if has_multiple_keys_openrouter() and rotate_openrouter_key():
                    time.sleep(retry_delay) # Delay before retrying
                    # No client to re-initialize for requests, just re-attempt with new key
                    continue
                else:
                    print("[WARN] No more OpenRouter keys to rotate, exhausting retries.")
            if attempt == max_retries - 1:
                raise Exception(f"Failed to generate component after {max_retries} attempts: {str(e)}")
            else:
                # For non-rate-limit errors, or if rotation failed, fail immediately
                raise Exception(f"Failed to generate component: {str(e)}")
        except Exception as e:
            last_error = e
            error_str = str(e)
            is_rate_limit = is_rate_limit_error_openrouter(e)
            is_permission = _is_permission_error(e)

            print(f"[WARN] Component generation attempt {attempt + 1} failed for {component_name}: {error_str[:200]}")

            if is_permission:
                print(f"[LOG] Permission error detected while generating {component_name}. Refreshing Bootstrap docs accessible to current key...")
                # This part needs adjustment, get_or_upload_bootstrap_docs currently expects genai.Client
                # For now, we will skip refreshing bootstrap docs with OpenRouter
                print("[WARN] Bootstrap doc refresh not supported with OpenRouter yet.")
                bootstrap_files.clear()
                use_bootstrap_docs = False
                continue

            if is_rate_limit and has_multiple_keys_openrouter() and attempt < max_retries - 1:
                print(f"[LOG] Rate limit detected, rotating to next key...")
                rotate_openrouter_key()
                time.sleep(retry_delay)
                # Bootstrap docs will not be reloaded for OpenRouter
                continue

            if has_multiple_keys_openrouter() and attempt < max_retries - 1:
                print(f"[LOG] Switching to next key to retry component generation...")
                rotate_openrouter_key()
                time.sleep(retry_delay)
                # Bootstrap docs will not be reloaded for OpenRouter
                continue

            print(f"[ERROR] Failed to generate component {component_name} after attempt {attempt + 1}: {error_str[:200]}")

    if use_bootstrap_docs:
        print(f"[WARN] Attempting final fallback for {component_name} without Bootstrap docs...")
        try:
            messages = [
                {"role": "user", "content": [{"type": "text", "text": item}]} for item in build_contents(include_bootstrap=False)
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
                "max_tokens": 16000
            }

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload)
            )
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

            response_json = response.json()

            if response_json.get('choices') and response_json['choices'][0].get('message') and response_json['choices'][0]['message'].get('content'):
                component_code = response_json['choices'][0]['message']['content'].strip()
                if '```html' in component_code:
                    component_code = component_code.split('```html')[1].split('```')[0].strip()
                elif '```' in component_code:
                    component_code = component_code.split('```')[1].split('```')[0].strip()
                print(f"[LOG] ✓ Successfully generated component without Bootstrap docs: {component_name}")
                return component_code
        except Exception as fallback_error:
            print(f"[ERROR] Fallback without Bootstrap docs failed for {component_name}: {fallback_error}")
            last_error = fallback_error

    if last_error:
        import traceback
        traceback.print_exc()
    return None


async def generate_all_components(plan_data: Dict, form_data: Dict, image_urls: List[str],
                           logo_url: str, favicon_url: str, theme_color: str,
                           font_name: str, business_category: str, business_sub_category: str,
                           openai_client: OpenAI, # Add openai_client for image generation
                           openrouter_key: str, # Add openrouter_key for text generation
                           image_prompts_info: Optional[Dict] = None) -> Dict[str, str]:
    """
    Generate all 8 components (4 fixed + 4 dynamic) in proper order
    NOW GENERATES IMAGES ON-DEMAND before each component that needs one
    
    Returns:
        Dictionary mapping component names to their HTML code
    """
    components = {}
    
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize OpenRouter key for component generation (Gemini via OpenRouter)
        # openrouter_key = get_openrouter_key() # Fetch key from environment
        # if not openrouter_key:
        #     raise Exception("OPENROUTER_API_KEY not configured for component generation")
        
        # Get Bootstrap docs (will be passed to generate_component)
        # Note: get_or_upload_bootstrap_docs currently expects genai.Client. 
        # For OpenRouter, we will pass the key directly, and eventually adapt this utility.
        bootstrap_files = [] # Initialize empty for now
        # TODO: Adapt get_or_upload_bootstrap_docs to work with OpenRouter or remove if not needed.

        # Get all_components from plan (new structure)
        all_components_from_plan = plan_data.get('all_components', [])
        
        # If all_components not present, build from old structure (backward compatibility)
        if not all_components_from_plan:
            print("[LOG] Using backward-compatible component structure")
            fixed_components = [
                {
                    "name": "Navigation",
                    "purpose": "Fixed navigation bar with logo and navigation links",
                    "order": 1,
                    "needs_image": False
                },
                {
                    "name": "Hero",
                    "purpose": "Hero section with hero image, headline, and call-to-action",
                    "order": 2,
                    "needs_image": True
                },
                {
                    "name": "Contact",
                    "purpose": "Contact form with mailto: link (form onsubmit uses mailto:EMAIL with subject and body), address display, phone, email, and optional Google Maps embed for location",
                    "order": 7,
                    "needs_image": False
                },
                {
                    "name": "Footer",
                    "purpose": "Footer with social links, copyright, and company information",
                    "order": 8,
                    "needs_image": False
                }
            ]
            
            # Dynamic components from plan (should have orders 3, 4, 5, 6)
            dynamic_components = plan_data.get('dynamic_components', [])
            
            # Ensure dynamic components have proper order (3-6)
            for idx, comp in enumerate(dynamic_components):
                if 'order' not in comp or comp.get('order', 0) < 3:
                    comp['order'] = 3 + idx
            
            # Combine all components and sort by order
            all_components_from_plan = fixed_components + dynamic_components
        
        all_components_from_plan.sort(key=lambda x: x.get('order', 999))
        
        # Track generated images
        generated_image_urls = list(image_urls) if image_urls else []
        
        # Get image prompts info from plan
        if not image_prompts_info:
            image_prompts_info = plan_data.get('image_plan', {})
        
        # Generate all components in order WITH ON-DEMAND IMAGE GENERATION
        print(f"[LOG] Generating {len(all_components_from_plan)} components in order...")
        for comp in all_components_from_plan:
            comp_name = comp.get('name', 'Unknown')
            comp_purpose = comp.get('purpose', 'Component')
            comp_order = comp.get('order', 999)
            needs_image = comp.get('needs_image', False)
            
            # STEP 1: Generate image on-demand if this component needs one (using OpenAI client)
            if needs_image:
                print(f"[LOG] Component {comp_order} ({comp_name}) needs an image - generating now...")
                image_url = generate_image_for_component(
                    component_info=comp,
                    business_category=business_category,
                    business_sub_category=business_sub_category,
                    theme_color=theme_color,
                    timestamp=timestamp,
                    openai_client=openai_client # Pass openai_client for image generation
                )
                
                if image_url:
                    generated_image_urls.append(image_url)
                    print(f"[LOG] ✓ Image generated for {comp_name}: {image_url}")
                else:
                    print(f"[WARN] Failed to generate image for {comp_name}, continuing without image...")
            
            # Get design info for this component
            component_design_info = {
                'design_style': comp.get('design_style', ''),
                'layout_type': comp.get('layout_type', ''),
                'visual_features': comp.get('visual_features', ''),
                'image_dimensions': comp.get('image_dimensions', ''),
                'image_usage': comp.get('image_usage', '')
            }
            
            # STEP 2: Generate component HTML (using OpenRouter key)
            print(f"[LOG] Generating component {comp_order}: {comp_name}...")
            
            # Pass logo_url and favicon_url directly
            comp_code = await generate_component(
                component_name=comp_name,
                component_purpose=comp_purpose,
                form_data=form_data,
                image_urls=generated_image_urls,  # Pass all generated images so far
                theme_color=theme_color,
                font_name=font_name,
                business_category=business_category,
                business_sub_category=business_sub_category,
                openrouter_key=openrouter_key, # Pass the openrouter_key here
                logo_url=logo_url,  # Pass the logo_url to individual component generation
                favicon_url=favicon_url, # Pass the favicon_url to individual component generation
                bootstrap_files=bootstrap_files,
                component_design_info=component_design_info,
                image_prompts_info=image_prompts_info
            )
            
            if comp_code:
                print(f"[LOG] Raw HTML for {comp_name} component:\n{comp_code[:1000]}...\n") # Log first 1000 chars
                components[comp_name] = comp_code
                print(f"[LOG] ✓ Component {comp_order} ({comp_name}) generated successfully")
        
        # Verify Contact and Footer are present
        if 'Contact' not in components:
            print("[ERROR] Contact component is missing! Regenerating...")
            # Try to regenerate Contact
            contact_comp = next((c for c in all_components_from_plan if c.get('name') == 'Contact'), None)
            if contact_comp:
                contact_code = await generate_component(
                    component_name='Contact',
                    component_purpose=contact_comp.get('purpose', 'Contact form with mailto: link'),
                    form_data=form_data,
                    image_urls=generated_image_urls,
                    logo_url=logo_url,
                    favicon_url=favicon_url, # Pass favicon_url
                    theme_color=theme_color,
                    font_name=font_name,
                    business_category=business_category,
                    business_sub_category=business_sub_category,
                    openrouter_key=openrouter_key, # Pass openrouter_key
                    bootstrap_files=bootstrap_files,
                    component_design_info=None,
                    image_prompts_info=image_prompts_info
                )
                if contact_code:
                    components['Contact'] = contact_code
                    print("[LOG] ✓ Contact component regenerated successfully")
        
        if 'Footer' not in components:
            print("[ERROR] Footer component is missing! Regenerating...")
            # Try to regenerate Footer
            footer_comp = next((c for c in all_components_from_plan if c.get('name') == 'Footer'), None)
            if footer_comp:
                footer_code = await generate_component(
                    component_name='Footer',
                    component_purpose=footer_comp.get('purpose', 'Footer with social links, copyright, and company information'),
                    form_data=form_data,
                    image_urls=generated_image_urls,
                    logo_url=logo_url,
                    favicon_url=favicon_url, # Pass favicon_url
                    theme_color=theme_color,
                    font_name=font_name,
                    business_category=business_category,
                    business_sub_category=business_sub_category,
                    openrouter_key=openrouter_key, # Pass openrouter_key
                    bootstrap_files=bootstrap_files,
                    component_design_info=None,
                    image_prompts_info=image_prompts_info
                )
                if footer_code:
                    components['Footer'] = footer_code
                    print("[LOG] ✓ Footer component regenerated successfully")
        
        print(f"[LOG] Successfully generated {len(components)}/{len(all_components_from_plan)} components")
        print(f"[LOG] Components present: {list(components.keys())}")
        print(f"[LOG] Total images generated on-demand: {len(generated_image_urls)}")
        
        # Final verification
        required_components = ['Navigation', 'Hero', 'Contact', 'Footer']
        missing_required = [c for c in required_components if c not in components]
        if missing_required:
            print(f"[ERROR] Missing required components: {missing_required}")
        
        # Store generated images in components dict (for backward compatibility)
        components['__generated_images__'] = generated_image_urls
        
        return components
        
    except Exception as e:
        print(f"[ERROR] Error generating components: {e}")
        import traceback
        traceback.print_exc()
        return components

