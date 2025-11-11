"""Component planning system for website generation"""

import json
from typing import Dict, List, Optional
# from google import genai # Comment out direct Gemini import
# from google.genai import types # Comment out types for Gemini config
import os
import requests # Import requests for OpenRouter
import time # Import time for rate limit delay
from utils.api_keys import (
    # get_gemini_key, rotate_gemini_key, is_rate_limit_error_gemini, has_multiple_keys_gemini, # Comment out direct Gemini key functions
    get_openrouter_key, rotate_openrouter_key, is_rate_limit_error_openrouter, has_multiple_keys_openrouter, 
    _key_manager
) # Use OpenRouter key functions


def get_planning_prompt(form_data: Dict) -> str:
    """Generate prompt for planning website components"""
    business_name = form_data.get('siteName', 'Business')
    business_category = form_data.get('businessCategory', '')
    business_sub_category = form_data.get('businessSubCategory', '')
    about_business = form_data.get('aboutBusiness', '')
    services_text = form_data.get('services', '')
    services_list = [s.strip() for s in services_text.split('\n') if s.strip()] if services_text else []
    theme_color = form_data.get('themeColor', '#4f46e5')
    
    return f"""You are an expert web developer planning a professional website structure with TRENDING 2024-2025 design patterns.

BUSINESS INFORMATION:
- Business Name: {business_name}
- Industry Category: {business_category}
- Sub Category: {business_sub_category}
- About Business: {about_business}
- Services: {chr(10).join(f"  • {s}" for s in services_list) if services_list else "Not specified"}
- Theme Color: {theme_color}

YOUR TASK:
1. Analyze the business category "{business_category}" and subcategory "{business_sub_category}"
2. Decide on 4 dynamic components that would be most valuable for this specific industry
3. ORDER THE 4 DYNAMIC COMPONENTS PROPERLY (order 3, 4, 5, 6) to create a MEANINGFUL WEBSITE FLOW:
   - Think about what makes sense for a professional business website
   - Typical good order: About/Services → Features/Benefits → Social Proof (Testimonials/Portfolio) → Final CTA
   - For restaurants: Menu → Gallery → Testimonials → Reservations
   - For tech companies: Services → Features → Case Studies → Pricing
   - For agencies: About → Portfolio → Process → Testimonials
   - IMPORTANT: Order components so the website tells a coherent story from top to bottom
4. Assign UNIQUE, LATEST TRENDING design styles to each component (NO REPETITION):
   - Choose style names from the curated 2025 trend library below. Select the style that BEST matches the component type and industry.
   - **HERO STYLES**: Glassmorphism Hero, 3D Parallax Hero, AI/Neon Glow Hero, Split Screen Hero, Animated Background Hero
   - **NAVIGATION STYLES**: Floating Glass Navbar, Sticky Smart Navbar, Bottom Icon Navbar, Mega Menu with Icons
   - **CARDS & CONTENT BLOCKS**: Glassmorphism Cards, 3D Tilt Cards, Gradient Border Cards, Magnetic Hover Cards, Dynamic Blob Cards
   - **IMAGERY/GALLERIES**: Masonry Grid Gallery, Hover Zoom + Blur Gallery, 3D Carousel Gallery, Scroll-triggered Reveal Gallery
   - **BUTTONS & MICRO-INTERACTIONS**: Gradient Glow Buttons, Magnetic Buttons, Neumorphic Buttons, Animated Border Buttons
   - **TESTIMONIALS/SOCIAL PROOF**: 3D Rotating Testimonials, Speech Bubble Testimonials, Gradient Frame Testimonials
   - **CTA/CONVERSION SECTIONS**: Split Gradient CTA, Glass CTA with Floating Icons, Motion Background CTA
   - **BACKGROUND STYLES**: Aurora Gradient Animation, Liquid Morphing Background, Noise Texture Gradient, Particle/Line Motion Backgrounds
   - **FEATURE/PROCESS LAYOUTS**: Floating Icon Feature Cards, Animated Timeline, Scroll-triggered Counter Grid, Lottie Illustration Showcase
   - BONUS IDEAS: Animated text effects, interactive pricing tables, AI chat bubble widgets, dark/light theme switchers, floating action buttons
   - Each component MUST use a DIFFERENT style name (strictly NO duplication). Set `design_style` to include the exact style name + short descriptor.
   - Components should NOT look the same - each needs unique visual identity, interactive polish, and modern styling comparable to award-winning 2025 websites (Apple, Stripe, Linear, Vercel, etc.)
5. For EACH of the 8 components, decide if it needs an image:
   - Navigation: NO (uses logo uploaded by user)
   - Hero: YES (ALWAYS needs hero banner image)
   - 4 Dynamic components: Decide individually based on component type and industry
   - Contact: NO
   - Footer: NO
5. For each component that needs an image, generate:
   - Detailed image generation prompt (relevant to category/subcategory, NOT user-specific text)
   - Image dimensions (e.g., 1920x600, 1200x800, 800x600, 600x600)
   - Aspect ratio (e.g., 16:9, 4:3, 1:1, 16:5)
   - How the image should be used in the component

COMPONENT STRUCTURE:
- Fixed Components (already decided):
  1. Navigation/Header - Logo from user (no generated image)
  2. Hero - MUST have hero image
  3. Contact - NO image
  4. Footer - NO image

- Dynamic Components (YOU DECIDE 4 based on category/subcategory):
  Based on {business_category} - {business_sub_category}, choose 4 components that make sense:
  Examples: Services, About, Features, Portfolio, Testimonials, Team, Process, Pricing, FAQ, Gallery, Menu, Stats, CTA, Timeline, etc.
  These MUST be tailored to the specific industry combination.
  
  CRITICAL - PROPER ORDERING (orders 3, 4, 5, 6):
  - Order 3: Usually About, Services, or What We Do (introduce the business)
  - Order 4: Usually Features, Benefits, or Services Details (show value)
  - Order 5: Usually Portfolio, Testimonials, Case Studies (build trust/social proof)
  - Order 6: Usually CTA, Pricing, FAQ, or Team (conversion/final push)
  - Make sure the flow makes logical sense for {business_category} - {business_sub_category}
  
  For EACH dynamic component, decide if it needs an image.

IMAGE PLANNING - ON-DEMAND GENERATION:
- We will generate images ON-DEMAND as we build each component
- Total images to generate: 1 (Hero) + 0-4 (dynamic components that need images)
- Hero Image: ALWAYS required - rectangular banner (1920x600 recommended)
- Dynamic Component Images: Decide individually for each of the 4 dynamic components
- Each image prompt should focus on the INDUSTRY/CATEGORY, not specific business details
- Images should be visually relevant to {business_category} - {business_sub_category}

OUTPUT FORMAT (JSON only, no markdown):
{{
  "all_components": [
    {{
      "name": "Navigation",
      "purpose": "Navigation bar with logo and menu links",
      "order": 1,
      "needs_image": false,
      "design_style": "Modern sticky navigation with backdrop blur"
    }},
    {{
      "name": "Hero",
      "purpose": "Hero section with banner image",
      "order": 2,
      "needs_image": true,
      "image_prompt": "Generate 1 professional, high-quality RECTANGULAR hero banner image (1920x600 pixels, 16:5 aspect ratio) that visually represents the business category '{business_category}' and subcategory '{business_sub_category}'. CRITICAL: Focus on the BUSINESS CATEGORY and SUBCATEGORY industry, NOT specific services. Ultra-professional, premium business quality. Modern, sleek, visually stunning. Clean composition with space for text overlay. Theme color: {theme_color}. Industry-specific imagery for {business_category} - {business_sub_category} category.",
      "image_dimensions": "1920x600",
      "image_aspect_ratio": "16:5",
      "image_usage": "Full-width hero banner with text overlay",
      "design_style": "Hero section with latest 2024-2025 trending design (animated gradients, floating elements, or 3D effects)"
    }},
    {{
      "name": "Dynamic Component 1 Name",
      "purpose": "What this component does for this business type",
      "order": 3,
      "needs_image": true/false,
      "image_prompt": "IF needs_image=true: Detailed prompt for generating professional image for {business_category} - {business_sub_category}. Include dimensions (e.g., 1200x800 pixels), aspect ratio (e.g., 3:2), style (professional, modern, business-appropriate), color scheme matching theme {theme_color}, and industry relevance. Focus on CATEGORY/SUBCATEGORY, not specific business details.",
      "image_dimensions": "e.g., 1200x800, 800x600, 600x600",
      "image_aspect_ratio": "e.g., 3:2, 4:3, 1:1",
      "image_usage": "How image is used (background, side image, card image, overlay, grid item, etc.)",
      "design_style": "LATEST 2024-2025 trending style #1 (e.g., Bento Grid, Glassmorphism, 3D Cards, Aurora Background, etc.) - MUST be unique and modern",
      "layout_type": "Layout description (e.g., asymmetric grid, centered cards, split-screen, etc.)",
      "visual_features": "Specific modern features (e.g., micro-interactions, hover effects, animated gradients, floating shadows, etc.)"
    }},
    {{
      "name": "Dynamic Component 2 Name",
      "purpose": "What this component does",
      "order": 4,
      "needs_image": true/false,
      "image_prompt": "IF needs_image=true: [Image prompt following same format as above]",
      "image_dimensions": "e.g., 1200x800",
      "image_aspect_ratio": "e.g., 3:2",
      "image_usage": "How image is used",
      "design_style": "LATEST 2024-2025 trending style #2 - DIFFERENT from component 3 - must be unique",
      "layout_type": "Layout description",
      "visual_features": "Specific modern features"
    }},
    {{
      "name": "Dynamic Component 3 Name",
      "purpose": "What this component does",
      "order": 5,
      "needs_image": true/false,
      "image_prompt": "IF needs_image=true: [Image prompt]",
      "image_dimensions": "e.g., 800x600",
      "image_aspect_ratio": "e.g., 4:3",
      "image_usage": "How image is used",
      "design_style": "LATEST 2024-2025 trending style #3 - DIFFERENT from components 3 and 4",
      "layout_type": "Layout description",
      "visual_features": "Specific modern features"
    }},
    {{
      "name": "Dynamic Component 4 Name",
      "purpose": "What this component does",
      "order": 6,
      "needs_image": true/false,
      "image_prompt": "IF needs_image=true: [Image prompt]",
      "image_dimensions": "e.g., 1200x800",
      "image_aspect_ratio": "e.g., 3:2",
      "image_usage": "How image is used",
      "design_style": "LATEST 2024-2025 trending style #4 - DIFFERENT from all previous components",
      "layout_type": "Layout description",
      "visual_features": "Specific modern features"
    }},
    {{
      "name": "Contact",
      "purpose": "Contact form with mailto functionality",
      "order": 7,
      "needs_image": false,
      "design_style": "Clean contact form with modern styling"
    }},
    {{
      "name": "Footer",
      "purpose": "Footer with social links and copyright",
      "order": 8,
      "needs_image": false,
      "design_style": "Modern footer with social icons"
    }}
  ],
  "notes": "Industry-specific components for {business_category} - {business_sub_category}. Each component has UNIQUE trending 2024-2025 design style. Images planned for on-demand generation."
}}

CRITICAL REQUIREMENTS:
- ALL 8 components MUST be listed in "all_components" array (Navigation, Hero, 4 dynamic, Contact, Footer)
- Dynamic components MUST be different for different category/subcategory combinations
- COMPONENT ORDERING IS CRITICAL: The 4 dynamic components (orders 3-6) MUST be ordered to create a LOGICAL, MEANINGFUL website flow
  * Order should tell a coherent story: Introduction → Value Proposition → Social Proof → Conversion
  * Think like a professional web designer creating a real business website
  * Example good flow: Hero → About → Services → Portfolio → Testimonials → Contact
  * Example bad flow: Hero → Testimonials → About → Services (testimonials before explaining what you do)
- Each component MUST have a UNIQUE, LATEST 2024-2025 trending design style (NO REPETITION)
- Use modern design trends: Bento Grid, Glassmorphism, 3D Cards, Aurora Backgrounds, Animated Gradients, Floating Elements, Micro-interactions, Claymorphism, Y2K aesthetics, etc.
- Components should NOT look the same - each needs unique visual identity, layout, and styling
- For components with needs_image=true, include detailed image_prompt with dimensions and aspect ratio
- Image prompts should focus on industry/type, NOT specific business details
- All components should use theme color {theme_color} in shades/variations
- Hero ALWAYS has needs_image=true
- Navigation, Contact, Footer ALWAYS have needs_image=false
- Dynamic components: decide individually if they need images based on component type and industry
- Return ONLY valid JSON, no markdown, no explanations"""


def plan_website_components(form_data: Dict) -> Dict:
    """
    Plan website components using LLM
    
    Returns:
        Dict with:
        - dynamic_components: List of 4 dynamic components
        - image_plan: Hero + 2 additional image prompts
        - component_order: Order of all 8 components
    """
    try:
        openrouter_key = get_openrouter_key()
        if not openrouter_key:
            raise Exception("OPENROUTER_API_KEY not configured")
        
        print("[LOG] Planning website components...")
        
        # Get planning prompt
        planning_prompt = get_planning_prompt(form_data)
        
        # Generate plan with retry on rate limit
        if _key_manager.openrouter_manager is None:
            # Ensure _key_manager is initialized
            _ = get_openrouter_key() 

        all_keys = _key_manager.openrouter_manager.get_all_keys()
        max_retries = len(all_keys) if all_keys else 1
        
        for attempt in range(max_retries):
            try:
                print(f"[LOG] Planning attempt {attempt + 1}/{max_retries}...")
                
                messages = [
                    {"role": "user", "content": [{"type": "text", "text": planning_prompt}]}
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
                    "max_tokens": 4000 # Max output tokens for planning
                }

                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    data=json.dumps(payload)
                )
                response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
                
                response_json = response.json()

                if not response_json.get('choices') or not response_json['choices'][0].get('message') or not response_json['choices'][0]['message'].get('content'):
                    raise Exception("No response from OpenRouter/Gemini")
                
                plan_text = response_json['choices'][0]['message']['content'].strip()
                
                # Clean up markdown code blocks if present
                if '```json' in plan_text:
                    plan_text = plan_text.split('```json')[1].split('```')[0].strip()
                elif '```' in plan_text:
                    plan_text = plan_text.split('```')[1].split('```')[0].strip()
                
                # Parse JSON
                plan_data = json.loads(plan_text)
                
                # Validate structure
                if 'all_components' not in plan_data:
                    raise Exception("Invalid plan: missing all_components")
                if len(plan_data['all_components']) != 8:
                    raise Exception(f"Invalid plan: expected 8 components, got {len(plan_data['all_components'])}")
                
                # Extract dynamic components (components 3-6) for backward compatibility
                all_components = plan_data['all_components']
                dynamic_components = [c for c in all_components if c.get('order', 0) in [3, 4, 5, 6]]
                
                # Create backward-compatible structure
                plan_data['dynamic_components'] = dynamic_components
                
                # Build image_plan for backward compatibility (will be replaced with on-demand generation)
                image_plan = {}
                for comp in all_components:
                    if comp.get('needs_image'):
                        comp_name = comp.get('name', '')
                        if comp_name == 'Hero':
                            image_plan['hero_image'] = {
                                'purpose': 'Hero section banner',
                                'prompt': comp.get('image_prompt', ''),
                                'dimensions': comp.get('image_dimensions', '1920x600'),
                                'aspect_ratio': comp.get('image_aspect_ratio', '16:5')
                            }
                
                plan_data['image_plan'] = image_plan
                
                print(f"[LOG] Successfully planned {len(all_components)} total components ({len(dynamic_components)} dynamic)")
                print(f"[LOG] Components: {[c['name'] for c in all_components]}")
                print(f"[LOG] Components with images: {[c['name'] for c in all_components if c.get('needs_image')]}")
                
                return plan_data
                
            except requests.exceptions.HTTPError as e:
                print(f"[WARN] HTTP Error from OpenRouter: {e.response.status_code} - {e.response.text[:200]}")
                if _key_manager.openrouter_manager.is_rate_limit_error(e):
                    print("[LOG] Rate limit detected from OpenRouter, rotating to next key...")
                    if has_multiple_keys_openrouter() and rotate_openrouter_key():
                        time.sleep(5) # Delay before retrying
                        continue # Try again with the new key
                    else:
                        print("[WARN] No more OpenRouter keys to rotate, exhausting retries.")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to plan website components after {max_retries} attempts: {str(e)}")
                else:
                    # For non-rate-limit errors, or if rotation failed, fail immediately
                    raise Exception(f"Failed to plan website components: {str(e)}")
            except Exception as e:
                error_str = str(e)
                is_rate_limit = is_rate_limit_error_openrouter(e) # Use OpenRouter rate limit checker
                
                print(f"[WARN] Planning attempt {attempt + 1} failed: {error_str[:200]}")
                
                if is_rate_limit and has_multiple_keys_openrouter() and attempt < max_retries - 1:
                    print(f"[LOG] Rate limit detected, rotating to next key...")
                    rotate_openrouter_key()
                    time.sleep(5) # Delay before retrying
                    continue
                elif attempt < max_retries - 1:
                    if has_multiple_keys_openrouter():
                        rotate_openrouter_key()
                        time.sleep(5) # Delay before retrying
                    continue
                else:
                    raise
        
        raise Exception("All planning attempts failed")
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse planning JSON: {e}")
        # Return fallback plan
        return get_fallback_plan(form_data)
    except Exception as e:
        print(f"[ERROR] Planning failed: {e}")
        # Return fallback plan
        return get_fallback_plan(form_data)


def get_fallback_plan(form_data: Dict) -> Dict:
    """Fallback plan if LLM planning fails"""
    business_category = form_data.get('businessCategory', 'Business')
    business_sub_category = form_data.get('businessSubCategory', 'Services')
    theme_color = form_data.get('themeColor', '#4f46e5')
    
    all_components = [
        {
            "name": "Navigation",
            "purpose": "Navigation bar with logo and menu links",
            "order": 1,
            "needs_image": False,
            "design_style": "Modern sticky navigation"
        },
        {
            "name": "Hero",
            "purpose": "Hero section with banner",
            "order": 2,
            "needs_image": True,
            "image_prompt": f"Professional rectangular hero banner (1920x600) for {business_category} - {business_sub_category} industry. Modern, sleek, professional quality with theme color {theme_color}.",
            "image_dimensions": "1920x600",
            "image_aspect_ratio": "16:5",
            "image_usage": "Full-width hero banner",
            "design_style": "Modern hero with gradient overlay"
        },
        {
            "name": "Services",
            "purpose": "Showcase business services",
            "order": 3,
            "needs_image": True,
            "image_prompt": f"Professional business image (1200x800) for {business_category} - {business_sub_category} services. Modern, business-appropriate, theme color {theme_color}.",
            "image_dimensions": "1200x800",
            "image_aspect_ratio": "3:2",
            "image_usage": "Side image or background",
            "design_style": "Card-based layout",
            "layout_type": "Grid layout",
            "visual_features": "Rounded corners, shadows"
        },
        {
            "name": "About",
            "purpose": "About the business",
            "order": 4,
            "needs_image": False,
            "design_style": "Split-screen layout",
            "layout_type": "Two-column",
            "visual_features": "Clean typography"
        },
        {
            "name": "Features",
            "purpose": "Key features or benefits",
            "order": 5,
            "needs_image": True,
            "image_prompt": f"Professional feature image (800x600) for {business_category} - {business_sub_category}. Modern, illustrative, theme color {theme_color}.",
            "image_dimensions": "800x600",
            "image_aspect_ratio": "4:3",
            "image_usage": "Feature illustration",
            "design_style": "Glassmorphism",
            "layout_type": "Three-column grid",
            "visual_features": "Glass effect, blur"
        },
        {
            "name": "Testimonials",
            "purpose": "Customer testimonials",
            "order": 6,
            "needs_image": False,
            "design_style": "Carousel layout",
            "layout_type": "Centered cards",
            "visual_features": "Quotes, avatars"
        },
        {
            "name": "Contact",
            "purpose": "Contact form with mailto",
            "order": 7,
            "needs_image": False,
            "design_style": "Modern form design"
        },
        {
            "name": "Footer",
            "purpose": "Footer with social links",
            "order": 8,
            "needs_image": False,
            "design_style": "Dark footer"
        }
    ]
    
    dynamic_components = [c for c in all_components if c.get('order', 0) in [3, 4, 5, 6]]
    
    return {
        "all_components": all_components,
        "dynamic_components": dynamic_components,
        "image_plan": {
            "hero_image": {
                "purpose": "Hero section banner",
                "prompt": f"Professional rectangular hero image for {business_category} - {business_sub_category} industry",
                "dimensions": "1920x600",
                "aspect_ratio": "16:5"
            }
        },
        "component_order": [1, 2, 3, 4, 5, 6, 7, 8],
        "notes": f"Fallback plan for {business_category} - {business_sub_category}"
    }

