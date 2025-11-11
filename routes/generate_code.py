"""Route for AI-powered HTML code generation"""

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
import json
from openai import OpenAI # Import OpenAI for image generation
from datetime import datetime
from utils.prompts import get_code_edit_prompt
from utils.constants import DEFAULT_COMPONENT
import time # Import time for delays
import requests # Import requests for OpenRouter
from utils.api_keys import (
    get_openai_key, rotate_openai_key, is_rate_limit_error_openai, has_multiple_keys_openai,
    # get_gemini_key, rotate_gemini_key, is_rate_limit_error_gemini, has_multiple_keys_gemini, # Comment out direct Gemini key functions
    get_openrouter_key, rotate_openrouter_key, is_rate_limit_error_openrouter, has_multiple_keys_openrouter,
    _key_manager
) # Use OpenAI and OpenRouter key functions
from utils.bootstrap_docs import get_or_upload_bootstrap_docs
from utils.wordpress_publisher import WordPressPublisher
from typing import Optional, List, Dict, Tuple
import re
import shutil


router = APIRouter()

@router.post("/edit_component")
async def edit_component(request: Request):
    """
    Edit the React component based on user instruction
    Input: { "prompt": "user instruction", "currentCode": "current JSX code" }
    Output: { "code": "updated JSX code" }
    """
    try:
        data = await request.json()
        user_prompt = data.get('prompt', '')
        current_code = data.get('currentCode', DEFAULT_COMPONENT)
        available_images = data.get('availableImages', [])
        print(f"[LOG] Received user edit prompt: {user_prompt}")
        print(f"[LOG] Available images: {len(available_images)}")
        if not user_prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Use _key_manager for OpenRouter (Gemini via OpenRouter)
        if _key_manager.openrouter_manager is None:
             _ = get_openrouter_key()
        openrouter_key = get_openrouter_key() # Use get_openrouter_key
        if not openrouter_key:
            raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured or no keys available.")

        try:
            print(f"[LOG] Generating component for prompt: {user_prompt[:50]}... with OpenRouter (Gemini)")
            
            # Prepare prompt for OpenRouter
            user_prompt_text = get_code_edit_prompt(user_prompt, current_code, available_images)
            system_message = "You are an expert web developer. Edit the provided code based on user instructions. Return only the updated code, no explanations."
            
            messages = [
                {"role": "system", "content": [{"type": "text", "text": system_message}]},
                {"role": "user", "content": [{"type": "text", "text": user_prompt_text}]}
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
                "max_tokens": 4096 # OpenRouter generally supports max_tokens, if not, remove.
            }

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload)
            )
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            
            response_json = response.json()

            if not response_json.get('choices') or not response_json['choices'][0].get('message') or not response_json['choices'][0]['message'].get('content'):
                raise HTTPException(status_code=500, detail="Failed to generate code: No response from OpenRouter/Gemini")
            
            generated_code = response_json['choices'][0]['message']['content'].strip()
            
            # Clean up markdown code blocks if present
            if generated_code.startswith('```'):
                lines = generated_code.split('\n')
                lines = lines[1:]
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                generated_code = '\n'.join(lines)
            print("[LOG] AI returned HTML website successfully")
            print(f"[LOG] Generated code for edit_component (first 500 chars): {generated_code[:500]}") # Added this line
            return JSONResponse({
                "code": generated_code.strip(),
                "success": True
            })
        except requests.exceptions.HTTPError as e:
            print(f"[WARN] HTTP Error from OpenRouter: {e.response.status_code} - {e.response.text[:200]}")
            if _key_manager.openrouter_manager.is_rate_limit_error(e) and has_multiple_keys_openrouter():
                # If rate limit and multiple keys, rotate and retry
                print("[LOG] Rate limit detected from OpenRouter, rotating to next key and retrying...")
                rotate_openrouter_key()
                time.sleep(5) # Delay before retrying
                # After rotation, re-fetch key and retry the whole process if possible
                # For now, just re-raise as the retry logic is handled upstream
                raise HTTPException(status_code=500, detail=f"Rate limit exceeded. Attempted to rotate key. Please retry.")
            else:
                raise HTTPException(status_code=500, detail=f"Failed to generate component: {str(e)}")
        except Exception as e:
            print(f"[ERROR] Error in edit_component generation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate component: {str(e)}")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"[ERROR] Error in edit_component: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create_website")
async def create_website(
    siteName: str = Form(...),
    businessSize: str = Form("Small"),
    themeColor: str = Form("#4f46e5"),
    fontName: str = Form("Inter"),
    businessCategory: str = Form(...),
    businessSubCategory: str = Form(...),
    businessAddress: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    facebook: str = Form(""),
    instagram: str = Form(""),
    linkedin: str = Form(""),
    twitter: str = Form(""),
    services: str = Form(""),
    extraPrompt: str = Form(""),
    aboutBusiness: str = Form(""),
    logoImage: Optional[UploadFile] = File(None),
    faviconImage: Optional[UploadFile] = File(None)
):
    try:
        # Prepare/validate form data
        form_data = {"siteName": siteName, "businessSize": businessSize, "themeColor": themeColor, "fontName": fontName, "businessCategory": businessCategory, "businessSubCategory": businessSubCategory, "businessAddress": businessAddress, "email": email, "phone": phone, "facebook": facebook, "instagram": instagram, "linkedin": linkedin, "twitter": twitter, "services": services, "extraPrompt": extraPrompt, "aboutBusiness": aboutBusiness}
        if not siteName:
            raise HTTPException(status_code=400, detail="Site name is required")
        if not businessCategory:
            raise HTTPException(status_code=400, detail="Business Category is required")
        if not businessSubCategory:
            raise HTTPException(status_code=400, detail="Business Sub Category is required")
        
        # Save logo
        os.makedirs('static/generated', exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logo_url, favicon_url = None, None

        if logoImage and logoImage.filename:
            filename = f"logo_{timestamp}_{logoImage.filename}"
            filename = filename.replace(" ", "_")
            filepath = os.path.join("static/generated", filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(logoImage.file, buffer)
            logo_url = f"/static/generated/{filename}"
            print(f"[LOG] Logo saved to: {filepath}, URL: {logo_url}") # Added logging
        
        if faviconImage and faviconImage.filename:
            filename = f"favicon_{timestamp}_{faviconImage.filename}"
            filename = filename.replace(" ", "_")
            filepath = os.path.join("static/generated", filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(faviconImage.file, buffer)
            favicon_url = f"/static/generated/{filename}"
            print(f"[LOG] Favicon saved to: {filepath}, URL: {favicon_url}") # Added logging
        
        # Step 2: Plan website components
        from utils.component_planner import plan_website_components
        
        print("[LOG] Step 2: Planning website components...")
        plan_data = plan_website_components(form_data)
        
        if not plan_data:
            raise HTTPException(status_code=500, detail="Failed to plan website components")
        
        print(f"[LOG] Planning complete: {len(plan_data.get('dynamic_components', []))} dynamic components")
        
        # Step 3: Images will be generated ON-DEMAND during component generation
        print("[LOG] Step 3: Images will be generated on-demand as components need them...")
        image_urls = []  # Will be populated by component generator
        
        # Step 4: Generate 8 components (with on-demand image generation)
        print("[LOG] Step 4: Generating 8 components...")
        
        from utils.component_generator import generate_all_components
        
        theme_color = form_data.get('themeColor', '#4f46e5')
        font_name = form_data.get('fontName', 'Inter')
        business_category = form_data.get('businessCategory', '')
        business_sub_category = form_data.get('businessSubCategory', '')
        
        # Get image plan from planning
        image_prompts_info = plan_data.get('image_plan', {})

        # Initialize OpenAI client for image generation
        openai_key_for_images = get_openai_key()
        if not openai_key_for_images:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured for image generation")
        openai_client = OpenAI(api_key=openai_key_for_images)
        
        # Initialize OpenRouter key for component generation (Gemini via OpenRouter)
        openrouter_key_for_text = get_openrouter_key() # Fetch key from environment
        if not openrouter_key_for_text:
            raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured for component generation")
        
        all_components = await generate_all_components(
            plan_data=plan_data,
            form_data=form_data,
            image_urls=image_urls,
            logo_url=logo_url if logo_url else '',
            favicon_url=favicon_url if favicon_url else '',
            theme_color=theme_color,
            font_name=font_name,
            business_category=business_category,
            business_sub_category=business_sub_category,
            openai_client=openai_client, # Pass OpenAI client for image generation
            openrouter_key=openrouter_key_for_text, # Pass OpenRouter key for text generation
            image_prompts_info=image_prompts_info
        )
        
        if not all_components or len(all_components) < 4:
            raise HTTPException(status_code=500, detail=f"Failed to generate components. Only {len(all_components)} components generated.")
        
        # Extract generated images from components (new on-demand approach)
        if '__generated_images__' in all_components:
            image_urls = all_components.pop('__generated_images__')
            print(f"[LOG] Extracted {len(image_urls)} on-demand generated images")
        
        print(f"[LOG] Successfully generated {len(all_components)} components with {len(image_urls)} images")
        
        # Step 5: Combine all components into final HTML
        print("[LOG] Step 5: Combining all components into final HTML...")
        
        from utils.website_combiner import combine_components
        
        try:
            generated_code = combine_components(
                all_components=all_components,
                form_data=form_data,
                image_urls=image_urls,
                logo_url=logo_url if logo_url else '',
                favicon_url=favicon_url if favicon_url else '',
                theme_color=theme_color,
                font_name=font_name
            )
            
            if not generated_code:
                raise HTTPException(status_code=500, detail="Failed to combine components into final HTML")
            
            # Validate HTML structure
            if not generated_code or len(generated_code.strip()) < 100:
                raise Exception("Generated code is too short or empty. Please try again.")
            
            # Ensure basic HTML structure exists
            if '<html' not in generated_code.lower() or '<body' not in generated_code.lower():
                raise Exception("Generated code is missing required HTML structure (html, body tags)")
            
            # Ensure Bootstrap CSS is included
            if 'bootstrap' not in generated_code.lower() or 'cdn.jsdelivr.net/npm/bootstrap' not in generated_code.lower():
                print("[WARN] Bootstrap CSS not found in generated code, adding it...")
                bootstrap_css = '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">\n'
                bootstrap_js = '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>\n'
                if '</head>' in generated_code:
                    generated_code = generated_code.replace('</head>', bootstrap_css + '</head>')
                elif '<head>' in generated_code:
                    generated_code = generated_code.replace('<head>', '<head>\n' + bootstrap_css)
                if '</body>' in generated_code:
                    generated_code = generated_code.replace('</body>', bootstrap_js + '</body>')
                elif '<body>' in generated_code:
                    generated_code = generated_code.replace('<body>', '<body>\n' + bootstrap_js)
            
            print("[LOG] Website generated successfully with component-based approach")
            print(f"[LOG] Generated code length: {len(generated_code)} characters")
            print(f"[LOG] Generated images count: {len(image_urls)}")
            print(f"[LOG] Generated components count: {len(all_components)}")
            
            return JSONResponse({
                "code": generated_code.strip(),
                "images": image_urls,
                "success": True
            })
                
        except Exception as e:
            print(f"[ERROR] Failed to combine components: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Failed to generate website: {str(e)}")
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"[ERROR] Error in create_website: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/publish-to-wordpress")
async def publish_to_wordpress(request: Request):
    """
    Publish generated HTML website to WordPress
    Input: { "title": "Website Title", "htmlContent": "<full HTML>", "images": [{"url": "...", "filename": "..."}] }
    Output: { "success": true, "postUrl": "https://wordpress.apexneural.cloud/post-slug", "postId": 123 }
    """
    try:
        data = await request.json()
        title = data.get('title', '')
        html_content = data.get('htmlContent', '')
        images = data.get('images', [])
        
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        if not html_content:
            raise HTTPException(status_code=400, detail="HTML content is required")
        
        # Get WordPress credentials from environment
        # Using the credentials provided by user
        wp_url = os.getenv('WP_URL', 'https://wordpress.apexneural.cloud')
        wp_username = os.getenv('WP_USERNAME', 'admin')
        wp_password = os.getenv('WP_PASSWORD', 'PMPsX0IR4tx88cr2d8fW')
        # Default to False (Basic Auth with Application Password) for external API access
        # Cookie auth only works reliably within WordPress context
        use_cookie_auth = os.getenv('WP_USE_COOKIE_AUTH', 'false').lower() == 'true'
        
        # Note: The password should be an Application Password (not regular password)
        # Create one at: https://wordpress.apexneural.cloud/wp-admin/user-edit.php?user_id=1
        # Or: wp-admin -> Users -> Edit User -> Application Passwords
        
        if not wp_url or not wp_username or not wp_password:
            raise HTTPException(status_code=500, detail="WordPress credentials not configured. Please add WP_URL, WP_USERNAME, and WP_PASSWORD to .env file.")
        
        print(f"[LOG] Publishing to WordPress: {title}")
        print(f"[LOG] WordPress URL: {wp_url}")
        print(f"[LOG] WordPress Username: {wp_username}")
        print(f"[LOG] Authentication method: {'Cookie-based' if use_cookie_auth else 'Basic Auth (Application Password)'}")
        print(f"[LOG] Images to upload: {len(images)}")
        
        # Initialize WordPress publisher
        publisher = WordPressPublisher(wp_url, wp_username, wp_password, use_cookie_auth=use_cookie_auth)
        
        # Test connection first
        print("[LOG] Testing WordPress API connection...")
        connection_test = publisher.test_connection()
        if not connection_test.get('success'):
            error_msg = connection_test.get('message', 'Authentication failed')
            print(f"[ERROR] WordPress authentication failed: {error_msg}")
            
            # Provide helpful error message with suggestions
            if not use_cookie_auth:
                error_response = f"WordPress authentication failed: {error_msg}\n\n"
                error_response += "SOLUTION: Create an Application Password:\n"
                error_response += f"1. Go to: {wp_url}/wp-admin/user-edit.php?user_id=1 (or Users -> Edit User)\n"
                error_response += "2. Scroll to 'Application Passwords' section\n"
                error_response += "3. Create a new Application Password\n"
                error_response += "4. Copy the password and update WP_PASSWORD in .env file\n"
                error_response += "\nNote: Application Passwords are required for external REST API access (WordPress 5.6+)."
            else:
                error_response = f"WordPress cookie authentication failed: {error_msg}\n\n"
                error_response += "Cookie authentication may not work for external API access.\n"
                error_response += "SOLUTION: Use Application Password instead:\n"
                error_response += "1. Set WP_USE_COOKIE_AUTH=false in .env\n"
                error_response += f"2. Create Application Password at: {wp_url}/wp-admin/user-edit.php?user_id=1\n"
                error_response += "3. Update WP_PASSWORD with the Application Password"
            
            raise HTTPException(status_code=401, detail=error_response)
        else:
            print(f"[LOG] WordPress authentication successful: {connection_test.get('message')}")
        
        # Build backend base URL for resolving relative image paths
        backend_base_url = str(request.base_url).rstrip('/')
        if backend_base_url.startswith('http://'):
            backend_base_url = backend_base_url.replace('http://', 'https://', 1) if 'localhost' not in backend_base_url else backend_base_url
        
        # Upload images and build URL mapping
        image_url_mapping = {}
        
        # ALWAYS extract images from HTML content as well (in addition to provided images)
        # This ensures we catch ALL images, not just ones the frontend found
        print("[LOG] Extracting ALL images from HTML content...")
        
        # Extract from img tags
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        html_images = re.findall(img_pattern, html_content, re.IGNORECASE)
        
        # Extract from CSS url()
        css_pattern = r'url\(["\']?([^"\')]+)["\']?\)'
        css_images = re.findall(css_pattern, html_content, re.IGNORECASE)
        
        # Extract from srcset
        srcset_pattern = r'srcset=["\']([^"\']+)["\']'
        srcset_matches = re.findall(srcset_pattern, html_content, re.IGNORECASE)
        srcset_images = []
        for srcset in srcset_matches:
            # srcset format: "image1.jpg 1x, image2.jpg 2x"
            urls = [u.strip().split(' ')[0] for u in srcset.split(',')]
            srcset_images.extend(urls)
        
        # Combine all found images
        all_html_images = list(set(html_images + css_images + srcset_images))
        print(f"[LOG] Found {len(all_html_images)} unique images in HTML (img: {len(html_images)}, CSS: {len(css_images)}, srcset: {len(srcset_images)})")
        
        # Filter for local images (not data URIs, not external URLs)
        backend_url_check = backend_base_url.rstrip('/')
        local_images = []
        for url in all_html_images:
            # Skip data URIs
            if url.startswith('data:'):
                continue
            # Include relative paths
            if url.startswith('/static/') or url.startswith('../static/') or '/static/' in url:
                local_images.append(url)
                continue
            # Include absolute URLs that are our backend
            if url.startswith('http'):
                if '127.0.0.1' in url or 'localhost' in url or backend_url_check in url:
                    local_images.append(url)
                    continue
            # Include any image file extensions
            if re.search(r'\.(png|jpg|jpeg|gif|webp|svg)(\?|$)', url, re.IGNORECASE):
                local_images.append(url)
        
        print(f"[LOG] Filtered to {len(local_images)} local images to upload")
        
        # Merge with provided images (avoid duplicates)
        provided_urls = {img.get('url', '') for img in images if img.get('url')}
        html_image_list = [{'url': url, 'filename': url.split('/').pop().split('?')[0]} for url in local_images]
        
        # Combine, avoiding duplicates
        combined_images = []
        seen_urls = set()
        
        # Add provided images first
        for img in images:
            url = img.get('url', '')
            if url and url not in seen_urls:
                combined_images.append(img)
                seen_urls.add(url)
        
        # Add HTML-extracted images
        for img in html_image_list:
            url = img.get('url', '')
            # Normalize URL for comparison
            normalized = url.replace('../', '/')
            if normalized not in seen_urls and url not in seen_urls:
                combined_images.append(img)
                seen_urls.add(url)
                seen_urls.add(normalized)
        
        images = combined_images
        print(f"[LOG] Total images to process: {len(images)} (provided: {len(provided_urls)}, HTML-extracted: {len(local_images)}, combined: {len(images)})")
        
        for idx, image_info in enumerate(images, 1):
            image_url = image_info.get('url', '')
            filename = image_info.get('filename', '')
            
            if not image_url:
                print(f"[WARN] Image {idx}/{len(images)}: No URL provided, skipping")
                continue
            
            print(f"[LOG] [{idx}/{len(images)}] Processing image: {image_url}")
            if filename:
                print(f"[LOG]         Filename: {filename}")
            
            # Normalize the image URL to a consistent relative path key for local file access
            normalized_url_key = image_url

            # First, strip any backend_base_url prefix if present
            if backend_base_url and normalized_url_key.startswith(backend_base_url):
                normalized_url_key = normalized_url_key.replace(backend_base_url, '')
            
            # Then, ensure it starts with a single leading slash for internal consistency
            if not normalized_url_key.startswith('/'):
                normalized_url_key = '/' + normalized_url_key
            
            # Remove any remaining domain/port if it somehow made it here (e.g., from external sources)
            if '://' in normalized_url_key:
                try:
                    path_after_domain = normalized_url_key.split('://', 1)[1]
                    path_parts = path_after_domain.split('/', 1)
                    if len(path_parts) > 1:
                        normalized_url_key = '/' + path_parts[1]
                    else:
                        normalized_url_key = '/' # Should not happen for images
                except Exception as parse_error:
                    print(f"[WARN] Error parsing URL for local path: {normalized_url_key} - {parse_error}")
                    # Fallback to original, which will likely fail file access
            
            # Clean up potential double slashes, e.g., //static/generated
            normalized_url_key = normalized_url_key.replace('//static/', '/static/')

            # Store original_path for mapping if it's different from normalized_url_key
            original_path_for_mapping = None
            if image_url != normalized_url_key:
                original_path_for_mapping = image_url

            try:
                # Resolve local file path based on the normalized_url_key
                # e.g., /static/generated/image.png -> static/generated/image.png
                local_file_path_relative = normalized_url_key.lstrip('/') # Remove leading slash
                local_file_path = os.path.join(os.getcwd(), local_file_path_relative) # Get absolute path

                if not os.path.exists(local_file_path):
                    print(f"[WARN] Local image file not found for {normalized_url_key} at {local_file_path}")
                    continue # Skip to next image if local file not found

                # Read image data directly
                with open(local_file_path, "rb") as f:
                    image_data = f.read()

                # Determine MIME type
                mime_type = "image/jpeg" # Default
                if filename.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif filename.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = 'image/jpeg'
                elif filename.lower().endswith('.gif'):
                    mime_type = 'image/gif'
                elif filename.lower().endswith('.webp'):
                    mime_type = 'image/webp'

                # Upload image to WordPress using its raw data
                wp_media = publisher.upload_image(image_data, filename, mime_type)
                
                if wp_media:
                    # WordPress media object can have different URL fields
                    wp_image_url = None
                    if 'source_url' in wp_media:
                        wp_image_url = wp_media['source_url']
                    elif 'url' in wp_media:
                        wp_image_url = wp_media['url']
                    elif 'guid' in wp_media:
                        if isinstance(wp_media['guid'], dict) and 'rendered' in wp_media['guid']:
                            wp_image_url = wp_media['guid']['rendered']
                        elif isinstance(wp_media['guid'], str):
                            wp_image_url = wp_media['guid']
                    
                    if wp_image_url:
                        # Map the normalized relative URL to the WordPress URL
                        image_url_mapping[normalized_url_key] = wp_image_url
                        print(f"[LOG] ✓ Mapped: {normalized_url_key} -> {wp_image_url}")
                        
                        # Add original_path if it was different and not already mapped
                        if original_path_for_mapping and original_path_for_mapping not in image_url_mapping:
                            image_url_mapping[original_path_for_mapping] = wp_image_url
                            print(f"[LOG] ✓ Mapped original (full) URL: {original_path_for_mapping} -> {wp_image_url}")
                else:
                    print(f"[WARN] ✗ Failed to upload image: {image_url} - No response from WordPress")
                    print(f"[WARN]   Response keys: {list(wp_media.keys()) if isinstance(wp_media, dict) else 'Not a dict'}")
                    print(f"[WARN]   Response: {str(wp_media)[:500]}")
            except Exception as e:
                print(f"[WARN] ✗ Error uploading image {image_url}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"[LOG] Successfully uploaded {len(image_url_mapping)} images")
        
        # Publish HTML website to WordPress
        print("[LOG] Publishing HTML content to WordPress...")
        result = publisher.publish_html_website(
            html_content=html_content,
            title=title,
            image_url_mapping=image_url_mapping,
            categories=[33],
            tags=[34],
            status="publish"
        )
        
        print(f"[LOG] Successfully published to WordPress: {result.get('postUrl')}")
        
        return JSONResponse({
            "success": True,
            "postUrl": result.get('postUrl'),
            "postId": result.get('postId'),
            "message": "Website published successfully to WordPress"
        })
        
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"[ERROR] Error publishing to WordPress: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to publish to WordPress: {str(e)}")
