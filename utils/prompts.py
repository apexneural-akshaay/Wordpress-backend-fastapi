"""AI system prompts and helpers - Professional Website Development Standards"""

from typing import Dict, List, Optional

def get_planning_prompt(form_data, image_urls):
    """Prompt for Gemini to analyze business data and create a detailed component plan based on category/subcategory"""
    business_name = form_data.get('siteName', 'Business')
    business_category = form_data.get('businessCategory', '')
    business_sub_category = form_data.get('businessSubCategory', '')
    business_size = form_data.get('businessSize', 'Small') # Added
    about_business = form_data.get('aboutBusiness', '')
    services_text = form_data.get('services', '')
    services_list = [s.strip() for s in services_text.split('\n') if s.strip()] if services_text else []
    theme_color = form_data.get('themeColor', '#4f46e5')
    font_name = form_data.get('fontName', 'Inter')
    address = form_data.get('businessAddress', '') # Added
    email = form_data.get('email', '') # Added
    phone = form_data.get('phone', '') # Added
    facebook = form_data.get('facebook', '') # Added
    instagram = form_data.get('instagram', '') # Added
    linkedin = form_data.get('linkedin', '') # Added
    twitter = form_data.get('twitter', '') # Added
    extra_prompt = form_data.get('extraPrompt', '') # Added
    
    return f"""You are an expert web developer creating a professional, modern, and visually appealing website component plan.

CRITICAL REQUIREMENT: Different components MUST be generated for different category/subcategory combinations. 
The components for "{business_category}" - "{business_sub_category}" should be tailored specifically to this industry combination.

BUSINESS INFORMATION:
- Business Name: {business_name}
- Industry Category: {business_category}
- Sub Category: {business_sub_category}
- Business Size: {business_size} # Added
- About Business: {about_business}
- Services: {chr(10).join(f"  • {s}" for s in services_list) if services_list else "Not specified"}
- Address: {address} # Added
- Email: {email} # Added
- Phone: {phone} # Added
- Social Media: Facebook={facebook}, Instagram={instagram}, LinkedIn={linkedin}, Twitter={twitter} # Added
- Theme Color: {theme_color}
- Font: {font_name}
- Extra Prompt: {extra_prompt} # Added
- Images Available: {len(image_urls)} images (1 hero + {len(image_urls)-1} topic images focused on {business_category} - {business_sub_category})

YOUR TASK:
1. Analyze the specific industry combination: {business_category} - {business_sub_category}
2. Design components that are SPECIFIC to this category/subcategory combination
3. Consider industry-specific requirements:
   - Restaurants/Food: Menu sections, gallery, reservations
   - Technology/Software: Features, tech stack, case studies
   - Healthcare/Medical: Services, testimonials, appointment booking
   - Retail/E-commerce: Product showcase, shopping features
   - Professional Services: Portfolio, testimonials, expertise areas
   - Education/Training: Courses, curriculum, testimonials
   - Real Estate: Property listings, virtual tours, contact forms
   - And so on for other categories...
4. Create a detailed plan with component names, purposes, and industry-specific content
5. Ensure each component serves a unique purpose for this industry

OUTPUT FORMAT (JSON only, no markdown):
{{
  "components": [
    {{
      "name": "Navigation",
      "purpose": "Fixed navigation bar with links - Industry-specific navigation items",
      "order": 1,
      "category_specific": "Navigation tailored for {business_category} - {business_sub_category}"
    }},
    {{
      "name": "Hero",
      "purpose": "Above the fold section with headline and CTA - Industry-specific messaging",
      "order": 2,
      "category_specific": "Hero section showcasing {business_category} - {business_sub_category} industry"
    }},
    {{
      "name": "About",
      "purpose": "Business description and founder message - Industry context",
      "order": 3,
      "category_specific": "About section explaining {business_category} - {business_sub_category} expertise"
    }},
    {{
      "name": "PainPoints",
      "purpose": "Current situation section with customer pain points - Industry-relevant problems",
      "order": 4,
      "category_specific": "Pain points specific to {business_category} - {business_sub_category} customers"
    }},
    {{
      "name": "Benefits",
      "purpose": "Desired outcome section showing benefits - Industry-specific solutions",
      "order": 5,
      "category_specific": "Benefits relevant to {business_category} - {business_sub_category} industry"
    }},
    {{
      "name": "Services",
      "purpose": "Services or products showcase - Industry-specific presentation",
      "order": 6,
      "category_specific": "Services section tailored for {business_category} - {business_sub_category}"
    }},
    {{
      "name": "Contact",
      "purpose": "Contact form and information - Industry-appropriate contact methods",
      "order": 7,
      "category_specific": "Contact section suitable for {business_category} - {business_sub_category}"
    }},
    {{
      "name": "Footer",
      "purpose": "Footer with links and contact info - Industry-standard footer elements",
      "order": 8,
      "category_specific": "Footer with {business_category} - {business_sub_category} relevant links"
    }}
  ],
  "industry_notes": "Specific requirements and components needed for {business_category} - {business_sub_category} industry. Different components should be generated for different category/subcategory combinations.",
  "image_usage": "How to use the {len(image_urls)} images (all focused on {business_category} - {business_sub_category} category) in different components",
  "category_specific_components": "List any additional components that are specific to {business_category} - {business_sub_category} industry"
}}

IMPORTANT: The components must be DIFFERENT for each category/subcategory combination. A restaurant's components should differ from a tech company's components.

Return ONLY valid JSON, no markdown, no explanations."""

def get_component_generation_prompt(component_name, component_purpose, form_data, image_urls, logo_url, favicon_url, all_components_context, generated_components):
    """Prompt for generating individual components with full professional standards and category-specific requirements"""
    business_name = form_data.get('siteName', 'Business')
    business_category = form_data.get('businessCategory', '')
    business_sub_category = form_data.get('businessSubCategory', '')
    about_business = form_data.get('aboutBusiness', '')
    services_text = form_data.get('services', '')
    services_list = [s.strip() for s in services_text.split('\n') if s.strip()] if services_text else []
    theme_color = form_data.get('themeColor', '#4f46e5')
    font_name = form_data.get('fontName', 'Inter')
    address = form_data.get('businessAddress', '')
    email = form_data.get('email', '')
    phone = form_data.get('phone', '')
    
    hero_img = image_urls[0] if len(image_urls) > 0 else ''
    topic_images = image_urls[1:3] if len(image_urls) > 1 else []
    
    # Build context of already generated components
    context_summary = ""
    if generated_components:
        context_summary = "\n\nALREADY GENERATED COMPONENTS (for reference and consistency):\n"
        for comp_name, comp_code in generated_components.items():
            context_summary += f"\n--- {comp_name} Component ---\n{comp_code[:500]}...\n"
    
    return f"""Generate the "{component_name}" component for a professional landing page.

PROFESSIONAL WEBSITE DEVELOPMENT STANDARDS:

1. DESIGN STANDARDS:
   - Modern Aesthetic: Use contemporary design trends (2024-2025 standards)
   - Consistent Styling: Maintain uniform color schemes, typography, and spacing
   - Professional Layout: Implement proper grid systems, alignment, and visual hierarchy
   - Responsive Design: Ensure seamless work on mobile, tablet, and desktop
   - Visual Polish: Include subtle animations, hover effects, and transitions

2. COMPONENT STRUCTURE REQUIREMENTS:

   SPACING & LAYOUT:
   - Use consistent padding/margin values (multiples of 4px or 8px)
   - Implement proper container widths (max-width: 1280px or similar)
   - Maintain adequate whitespace between sections
   - Align elements properly using flexbox or grid
   - Standard spacing: py-16, py-20 for sections; px-4, px-6, px-8 for padding

   TYPOGRAPHY:
   - Use a clear font hierarchy (h1, h2, h3, p with distinct sizes)
   - Consistent font family: {font_name}
   - Proper line-height (1.5-1.7 for body text)
   - Appropriate font weights (400, 500, 600, 700)
   - Example: h1 (text-4xl or text-5xl), h2 (text-3xl), h3 (text-2xl), p (text-base)

   COLOR SCHEME:
   - Primary color: {theme_color}
   - Define consistent color palette using {theme_color} as primary
   - Proper contrast ratios for accessibility (WCAG AA minimum)
   - Consistent use of grays for text (text-gray-900, text-gray-700, text-gray-600)
   - Backgrounds: bg-white, bg-gray-50, bg-gray-100 for light sections

   VISUAL ELEMENTS:
   - Professional quality images (use provided images)
   - Consistent border-radius values (rounded-lg, rounded-xl)
   - Shadow styles that match across components (shadow-lg, shadow-xl)
   - Icon consistency (same library, same size proportions)

3. CATEGORY-SPECIFIC REQUIREMENT:
   - This component is for {business_category} - {business_sub_category} industry
   - Components MUST be different for different category/subcategory combinations
   - Tailor content, layout, and features specifically to this industry
   - Use industry-appropriate terminology, imagery, and structure

COMPONENT DETAILS:
- Component Name: {component_name}
- Purpose: {component_purpose}
- Industry: {business_category} - {business_sub_category}

BUSINESS INFORMATION (USE ALL OF THIS):
- Business Name: {business_name}
- About Business: {about_business}
- Services: {chr(10).join(f"  • {s}" for s in services_list) if services_list else "Not specified"}
- Address: {address}
- Email: {email}
- Phone: {phone}
- Theme Color: {theme_color}
- Font: {font_name}

AVAILABLE IMAGES (All focused on {business_category} - {business_sub_category} category):
- Hero Image: {hero_img if hero_img else 'N/A'} (use in Hero component only)
- Topic Image 1: {topic_images[0] if len(topic_images) > 0 else 'N/A'} (category/subcategory imagery)
- Topic Image 2: {topic_images[1] if len(topic_images) > 1 else 'N/A'} (category/subcategory imagery)

LOGO & FAVICON:
{f"Logo: {logo_url}" if logo_url else "No logo"}
{f"Favicon: {favicon_url}" if favicon_url else "No favicon"}

ALL COMPONENTS PLAN:
{all_components_context}

{context_summary}

CRITICAL REQUIREMENTS:
1. Return ONLY the HTML code for this component (no markdown, no backticks, no JSON)
2. Use TailwindCSS classes (CDN will be included in final HTML)
3. Component MUST be self-contained and properly structured
4. Use theme color {theme_color} appropriately as primary color
5. Use font {font_name} consistently
6. Industry-specific: Component MUST be tailored specifically to {business_category} - {business_sub_category}
7. Light backgrounds (bg-white, bg-gray-50) with dark text (text-gray-900)
8. Proper spacing: py-16, py-20 for sections; mb-8, mb-12 for margins
9. Container: container mx-auto max-w-7xl px-4 (or max-w-6xl for narrower layouts)
10. Responsive: Use sm:, md:, lg:, xl: breakpoints appropriately
11. If Navigation: Fixed nav with bg-{theme_color.replace('#', '')}/95 backdrop-blur-sm and white text
12. If Hero: Use hero image {hero_img} with proper aspect ratio and overlay
13. If Contact: Include form with Name, Email, Message fields, validation-ready structure
14. If Footer: Dark background (bg-gray-900) with white text
15. Add smooth transitions: transition-all duration-300
16. Include hover effects: hover:scale-105, hover:shadow-lg where appropriate
17. Semantic HTML: Use proper HTML5 semantic elements (header, nav, section, article, footer)
18. Accessibility: Include alt text for images, ARIA labels where needed
19. Visual hierarchy: Clear heading structure (h1 → h2 → h3)
20. Professional polish: Subtle shadows, rounded corners, smooth animations

COMPONENT-SPECIFIC INSTRUCTIONS:
- Ensure this component is UNIQUE to {business_category} - {business_sub_category} industry
- Different category/subcategory combinations should produce different component structures
- Use industry-appropriate content, imagery, and layout patterns

OUTPUT: Only the HTML code for {component_name} component, nothing else. No markdown, no explanations.

CRITICAL: 
- DO NOT write "[Previous Component HTML]" or any placeholders
- DO NOT write comments like "<!-- Component goes here -->"
- Write the ACTUAL HTML code for this component
- Include proper HTML structure with divs, sections, classes, etc.
- Make it a complete, self-contained component that can be inserted into a website"""

def get_combining_prompt(all_components, form_data, image_urls, logo_url, favicon_url):
    """Prompt for combining all components into final HTML - simplified, let Claude decide"""
    business_name = form_data.get('siteName', 'Business')
    business_category = form_data.get('businessCategory', '')
    business_sub_category = form_data.get('businessSubCategory', '')
    theme_color = form_data.get('themeColor', '#4f46e5')
    font_name = form_data.get('fontName', 'Inter')
    
    # Build components list with clear structure
    components_list = []
    for name, code in all_components.items():
        components_list.append(f"=== {name} Component ===\n{code}\n")
    components_html = "\n".join(components_list)
    
    return f"""CRITICAL TASK: Combine the HTML components below into ONE complete HTML document.

You MUST include the ACTUAL HTML CODE from each component below. DO NOT use placeholders like "[Previous Navigation Component HTML]" or "[Previous Hero Component HTML]". You MUST copy and paste the actual HTML code from each component into the final document.

Business: {business_name} ({business_category} - {business_sub_category})
Theme Color: {theme_color}
Font: {font_name}
{f"Logo: {logo_url}" if logo_url else ""}
{f"Favicon: {favicon_url}" if favicon_url else ""}
Images: {', '.join(image_urls) if image_urls else 'None'}

═══════════════════════════════════════════════════════════════
COMPONENTS TO COMBINE (INCLUDE ACTUAL HTML CODE FROM EACH):
═══════════════════════════════════════════════════════════════

{components_html}

═══════════════════════════════════════════════════════════════
REQUIREMENTS:
═══════════════════════════════════════════════════════════════

1. Copy the ACTUAL HTML code from "=== Navigation Component ===" and paste it into the final HTML
2. Copy the ACTUAL HTML code from "=== Hero Component ===" and paste it into the final HTML
3. Copy the ACTUAL HTML code from each component section and paste it into the final HTML
4. DO NOT write "[Previous Navigation Component HTML]" or any placeholders
5. DO NOT write comments like "<!-- Navigation Component -->" - include the actual HTML
6. Create a complete HTML document with <!DOCTYPE html>, <head>, <body>, and </html>
7. Include TailwindCSS CDN in <head>
8. Add custom CSS in <style> tag for smooth scrolling and animations
9. Add JavaScript in <script> tag before </body> for navigation, smooth scrolling, form handling
10. Ensure all sections have proper background colors (bg-white, bg-gray-50) so content is visible
11. Use the theme color {theme_color} appropriately
12. Use the font {font_name} consistently

CRITICAL: Every component section above contains actual HTML code. Copy that HTML code and paste it into the final document. DO NOT create placeholders or references.

Output ONLY the complete HTML code starting with <!DOCTYPE html> and ending with </html>. No explanations, no markdown, just the HTML code."""

def get_code_edit_prompt(user_prompt, current_code, available_images):
    """Returns a prompt for editing existing code using Gemini with professional standards"""
    return f"""Edit the following website code based on this request: {user_prompt}

PROFESSIONAL WEBSITE DEVELOPMENT STANDARDS:
- Maintain consistent styling (spacing, colors, typography)
- Ensure responsive design on all screen sizes
- Keep visual polish (animations, hover effects, transitions)
- Preserve accessibility features (alt tags, ARIA labels)
- Maintain professional layout and visual hierarchy

Current code:
{current_code}

Available images (all focused on business category/subcategory):
{chr(10).join(f"- {img}" for img in available_images)}

Make sure to:
1. Keep all existing functionality
2. Use TailwindCSS for styling
3. Maintain responsive design
4. Use provided images if relevant
5. Follow professional website development standards
6. Maintain consistency with existing design system
7. Return only the complete HTML code, no markdown or explanations
"""


def get_component_prompt(component_name: str, component_purpose: str, form_data: Dict, 
                        image_urls: List[str], logo_url: str, favicon_url: str, 
                        theme_color: str, font_name: str, business_category: str, business_sub_category: str,
                        component_design_info: Optional[Dict] = None,
                        image_prompts_info: Optional[Dict] = None) -> str:
    """Generate prompt for individual component generation using Bootstrap"""
    business_name = form_data.get('siteName', 'Business')
    business_size = form_data.get('businessSize', 'Small') # Added
    about_business = form_data.get('aboutBusiness', '')
    services_text = form_data.get('services', '')
    services_list = [s.strip() for s in services_text.split('\n') if s.strip()] if services_text else []
    address = form_data.get('businessAddress', '')
    email = form_data.get('email', '')
    phone = form_data.get('phone', '')
    facebook = form_data.get('facebook', '')
    instagram = form_data.get('instagram', '')
    linkedin = form_data.get('linkedin', '')
    twitter = form_data.get('twitter', '')
    extra_prompt = form_data.get('extraPrompt', '') # Added
    
    hero_image = image_urls[0] if len(image_urls) > 0 else ''
    additional_image_1 = image_urls[1] if len(image_urls) > 1 else ''
    additional_image_2 = image_urls[2] if len(image_urls) > 2 else ''
    
    # Create company name slug for navigation IDs (same as in combiner)
    company_slug = business_name.lower().replace(' ', '').replace('-', '').replace('_', '').replace('.', '').replace(',', '')[:20]
    
    # Get design style info for this component
    design_style = component_design_info.get('design_style', '') if component_design_info else ''
    layout_type = component_design_info.get('layout_type', '') if component_design_info else ''
    visual_features = component_design_info.get('visual_features', '') if component_design_info else ''
    image_dimensions = component_design_info.get('image_dimensions', '') if component_design_info else ''
    image_usage = component_design_info.get('image_usage', '') if component_design_info else ''
    
    # Get image prompt info
    image_prompt_text = ''
    if image_prompts_info:
        # Find which image is for this component
        if component_name.lower() not in ['navigation', 'hero', 'contact', 'footer']:
            # Check additional images
            if image_prompts_info.get('additional_image_1', {}).get('component', '').lower() == component_name.lower():
                img_info = image_prompts_info.get('additional_image_1', {})
                image_prompt_text = f"""
IMAGE PROMPT FOR THIS COMPONENT:
- Original Prompt: {img_info.get('prompt', '')}
- Dimensions: {img_info.get('dimensions', '')}
- Aspect Ratio: {img_info.get('aspect_ratio', '')}
- Style Notes: {img_info.get('style_notes', '')}
- Image URL: {additional_image_1}
- Recommended Usage: {image_usage if image_usage else img_info.get('purpose', '')}
- Image Dimensions: {image_dimensions if image_dimensions else img_info.get('dimensions', '')}
"""
            elif image_prompts_info.get('additional_image_2', {}).get('component', '').lower() == component_name.lower():
                img_info = image_prompts_info.get('additional_image_2', {})
                image_prompt_text = f"""
IMAGE PROMPT FOR THIS COMPONENT:
- Original Prompt: {img_info.get('prompt', '')}
- Dimensions: {img_info.get('dimensions', '')}
- Aspect Ratio: {img_info.get('aspect_ratio', '')}
- Style Notes: {img_info.get('style_notes', '')}
- Image URL: {additional_image_2}
- Recommended Usage: {image_usage if image_usage else img_info.get('purpose', '')}
- Image Dimensions: {image_dimensions if image_dimensions else img_info.get('dimensions', '')}
"""
    
    # Theme color shades
    theme_color_hex = theme_color.replace('#', '')
    
    # Build dynamic component specific instructions
    dynamic_component_instructions = ""
    if component_name.lower() not in ['navigation', 'header', 'nav', 'hero', 'contact', 'footer']:
        dynamic_component_instructions = f"""
**DYNAMIC COMPONENT**: Tailor specifically to {business_category} - {business_sub_category}. Use industry-appropriate content, layout, and terminology. {f"CRITICAL: This component MUST use the {design_style} design style - make it visually unique and different from other components. Implement {layout_type} layout with {visual_features}." if design_style else ""} {f"Use the provided image ({additional_image_1 if additional_image_1 else additional_image_2}) according to: {image_usage}. Image dimensions: {image_dimensions}. Ensure image is properly sized and integrated into the component design." if (additional_image_1 or additional_image_2) and image_usage else ""}

ADDITIONAL CONTEXT / EXTRA PROMPT: {extra_prompt}"""

    return f"""Generate the "{component_name}" component for a professional website.

COMPONENT DETAILS:
- Name: {component_name}
- Purpose: {component_purpose}
- Industry: {business_category} - {business_sub_category}
{f"- Design Style: {design_style} (TRENDING, UNIQUE style - implement this specific style)" if design_style else ""}
{f"- Layout Type: {layout_type}" if layout_type else ""}
{f"- Visual Features: {visual_features}" if visual_features else ""}

BUSINESS INFORMATION (USE ALL OF THIS):
- Business Name: {business_name}
- Business Size: {business_size} # Added
- About: {about_business}
- Services: {chr(10).join(f"  • {s}" for s in services_list) if services_list else "Not specified"}
- Address: {address}
- Email: {email}
- Phone: {phone}
- Social: Facebook={facebook}, Instagram={instagram}, LinkedIn={linkedin}, Twitter={twitter}
- Extra Prompt: {extra_prompt} # Added

DESIGN REQUIREMENTS - TRENDING 2025 WEB DESIGN:
🎨 YOU ARE AN EXPERT FRONTEND DESIGNER creating TRENDING, EYE-CATCHING components that look VISUALLY STUNNING and MODERN.

1. Use Bootstrap 5.3 (CDN will be included in final HTML)
2. {f"TRENDING DESIGN STYLE: {design_style} - CRITICAL - This component MUST use this specific trending design style. Research and implement this style properly (e.g., Glassmorphism = frosted glass effect with backdrop blur, Neumorphism = soft shadows and highlights, Gradient Mesh = colorful gradient overlays, Card-based = clean card layouts, etc.). This style must be UNIQUE and different from other components." if design_style else "Use a modern, professional design style"}

MODERN LAYOUT & VISUAL RULES (2025 Web Trends):
- Use modern layout styles: CSS Grid, Flexbox, Glassmorphism effects, Gradient overlays, Neumorphism, Minimal 3D shadows
- Include DYNAMIC ANIMATIONS and HOVER EFFECTS that feel smooth and premium
- Use BOLD TYPOGRAPHY with beautiful color contrast and modern UI patterns
- Create aesthetic, premium sections - NOT plain basic blocks
- Every section should look current with 2025 web design trends
- Design should look ready for a REAL BUSINESS landing page, not a sample template

3. Theme Color: {theme_color} - CRITICAL - use this and its shades throughout the ENTIRE component
   - Primary color: {theme_color} (for buttons, links, accents)
   - Light shade 1: 20% lighter than {theme_color} (for light backgrounds, hover states)
   - Light shade 2: 40% lighter than {theme_color} (for very light backgrounds)
   - Dark shade 1: 20% darker than {theme_color} (for hover effects, borders)
   - Dark shade 2: 40% darker than {theme_color} (for text on light backgrounds, emphasis)
   - Backgrounds: Use light tints of theme color (rgba with low opacity)
   - Buttons: Use {theme_color} with darker shade on hover
   - Links: Use {theme_color} color
   - Text: Dark text on light backgrounds, light text on dark theme sections
   - ALL colors in this component must relate to {theme_color} palette
4. Font: {font_name} (Google Fonts CDN will be included)
5. Include inline CSS in <style> tag within component - define theme color shades using CSS
6. Responsive: Use Bootstrap grid system (container, row, col)
7. Spacing: Minimum 80px padding top/bottom for sections
8. Professional: Modern, clean, VISUALLY STUNNING and PREMIUM
9. Color consistency: Every element should use theme color or its shades - no random colors
10. ANIMATIONS: Include smooth transitions, hover effects, micro-interactions
11. PREMIUM FEEL: Use shadows, gradients, backdrop blur, rounded corners strategically
12. REALISTIC CONTENT: Use complete, professional dummy content (not Lorem Ipsum)
13. **STRICT STYLE ENFORCEMENT**: Implement the exact style described in `design_style` from planning. No two components should share the same visual treatment.

TRENDING STYLE REFERENCE (CHOOSE MATCHING PATTERN):
- HERO: Glassmorphism Hero / 3D Parallax Hero / AI-Neon Glow Hero / Split Screen Hero / Animated Background Hero
- NAVIGATION: Floating Glass Navbar / Sticky Smart Navbar / Bottom Icon Navbar / Mega Menu with Icons
- CONTENT & CARDS: Glassmorphism Cards / 3D Tilt Cards / Gradient Border Cards / Magnetic Hover Cards / Dynamic Blob Cards
- IMAGES: Masonry Grid Gallery / Hover Zoom + Blur Gallery / 3D Carousel Gallery / Scroll Reveal Gallery
- BUTTONS: Gradient Glow Button / Magnetic Button / Neumorphic Button / Animated Border Button
- TESTIMONIALS: 3D Rotating Testimonials / Speech Bubble Testimonials / Gradient Frame Testimonials
- CTA: Split Gradient CTA / Glass CTA with Floating Icons / Motion Background CTA
- BACKGROUNDS: Aurora Gradient Animation / Liquid Morphing Background / Noise Texture Gradient / Particle-Line Motion Background
- FEATURE SECTIONS: Floating Icon Feature Grid / Animated Timeline / Scroll-triggered Counter Strip / Lottie Illustration Feature Block
- BONUS: Animated text sequences, interactive pricing toggles, AI chat bubble widget, dark/light mode switcher, floating action buttons

When implementing the style, incorporate the hallmark patterns (e.g., frosted glass panels for Glassmorphism, depth/tilt for 3D cards, animated gradients for neon glow, magnetic hover tracking for magnetic cards/buttons, etc.).
{f"10. Layout: {layout_type} - Implement this specific layout type" if layout_type else ""}
{f"11. Visual Features: {visual_features} - Include these specific visual features" if visual_features else ""}

AVAILABLE IMAGES:
- Hero Image: {hero_image if hero_image else 'N/A'} (use only in Hero component)
- Additional Image 1: {additional_image_1 if additional_image_1 else 'N/A'}
- Additional Image 2: {additional_image_2 if additional_image_2 else 'N/A'}
{image_prompt_text}

LOGO & FAVICON:
{f"Logo: {logo_url}" if logo_url else "No logo"} (CRITICAL: USE THIS PATH for the logo in the navigation/header)
{f"Favicon: {favicon_url}" if favicon_url else "No favicon"} (CRITICAL: USE THIS PATH for the favicon in the <head>)

COMPONENT-SPECIFIC INSTRUCTIONS:
{f'''**NAVIGATION/HEADER**: 🚨 CRITICAL NAVIGATION FORMAT 🚨
- ALL navigation links MUST use hash-based anchors with company slug prefix
- Company slug for this website: {company_slug}
- REQUIRED link format: #{company_slug}-home, #{company_slug}-about, #{company_slug}-services, #{company_slug}-contact
- Example: For "ABC Company", slug is "abccompany", links are: #abccompany-home, #abccompany-about, #abccompany-services, #abccompany-contact
- ❌ NEVER use relative paths: /home, /about, /services, /contact
- ❌ NEVER use plain anchors: #home, #about, #services, #contact
- ✅ ALWAYS use company slug prefix: #{company_slug}-home, #{company_slug}-about, #{company_slug}-services, #{company_slug}-contact
- Logo: {logo_url} with PROPER SIZING (height: 40-50px, clearly visible)
- Company name text: visible and readable (font-size: 18-24px)
- Sticky navbar with backdrop blur, theme color background
- Logo and company name MUST both be visible and properly sized
- This format is MANDATORY for proper navigation functionality in preview and WordPress''' if component_name.lower() in ['navigation', 'header', 'nav'] else ''}
{f'**HERO**: Use hero image {hero_image}, full-width banner with dark overlay (rgba(0,0,0,0.6)), white text, call-to-action button, category-relevant headline' if component_name.lower() == 'hero' else ''}
{f'**CONTACT**: CRITICAL - Contact form MUST use mailto: functionality. Form onsubmit handler MUST use: window.location.href = `mailto:{email}?subject=${{encodeURIComponent(subject)}}&body=${{encodeURIComponent(body)}}`; Include fields: Name (input), Email (input), Message (textarea). On form submit, construct mailto link with form data and redirect. Display contact info: Address: {address}, Phone: {phone}, Email: {email}. The email address for mailto MUST be: {email}. Optional: Google Maps embed for location {address}.' if component_name.lower() == 'contact' else ''}
{f'**FOOTER**: Create a COMPACT footer (max height 280px) with dark background and MINIMAL content. Layout should be a single row (or two narrow columns on mobile) containing only: small logo/company name, concise copyright line, and up to four social icons ({facebook}, {instagram}, {linkedin}, {twitter}). Use reduced padding (py-8 desktop, py-6 mobile) and smaller typography (text-sm / text-xs). No large paragraphs, no extra sections, no large margins. Make it visually balanced but lightweight.' if component_name.lower() == 'footer' else ''}
{dynamic_component_instructions}

OUTPUT REQUIREMENTS:
1. Return ONLY the HTML code for this component
2. Include inline CSS in <style> tag
3. Use Bootstrap classes for layout
4. Component must be self-contained
5. No markdown, no backticks, no JSON
6. Start with opening tag, end with closing tag
7. Use semantic HTML5 elements

🚨 CRITICAL NAVIGATION & ID REQUIREMENTS 🚨:
8. If Navigation component: 
   - Company slug: {company_slug}
   - ALL links MUST use format: #{company_slug}-home, #{company_slug}-about, #{company_slug}-services, #{company_slug}-contact
   - Example: <a href="#{company_slug}-home">Home</a>, <a href="#{company_slug}-about">About</a>, etc.
   - ❌ NEVER: /home, /about, #home, #about
   - ✅ ALWAYS use company slug prefix: #{company_slug}-home, #{company_slug}-about, #{company_slug}-services, #{company_slug}-contact
   
9. If Hero component: 
   - Add id="{company_slug}-home" to main section/container
   - Example: <section id="{company_slug}-home" class="...">
   
10. If Contact component: 
    - Add id="{company_slug}-contact" to main section/container
    - Example: <section id="{company_slug}-contact" class="...">
    
11. If other components (About, Services, Features, etc.): 
    - Add matching ID to main section/container
    - For About component: id="{company_slug}-about"
    - For Services component: id="{company_slug}-services"
    - For Features component: id="{company_slug}-features"
    - Pattern: id="{company_slug}-[component-name-lowercase]"
    - Company slug: {company_slug}

CRITICAL: Return the actual HTML code for {component_name} component, nothing else."""


def get_combination_prompt(all_components: Dict[str, str], form_data: Dict,
                           image_urls: List[str], logo_url: str, favicon_url: str,
                           theme_color: str, font_name: str) -> str:
    """Generate prompt for combining all components into final HTML"""
    business_name = form_data.get('siteName', 'Business')
    business_category = form_data.get('businessCategory', '')
    business_sub_category = form_data.get('businessSubCategory', '')
    business_size = form_data.get('businessSize', 'Small') # Added
    about_business = form_data.get('aboutBusiness', '') # Added
    services_text = form_data.get('services', '') # Added
    services_list = [s.strip() for s in services_text.split('\n') if s.strip()] if services_text else [] # Added
    address = form_data.get('businessAddress', '') # Added
    email = form_data.get('email', '') # Added
    phone = form_data.get('phone', '') # Added
    facebook = form_data.get('facebook', '') # Added
    instagram = form_data.get('instagram', '') # Added
    linkedin = form_data.get('linkedin', '') # Added
    twitter = form_data.get('twitter', '') # Added
    extra_prompt = form_data.get('extraPrompt', '') # Added
    
    # Create company name slug for navigation IDs
    company_slug = business_name.lower().replace(' ', '').replace('-', '').replace('_', '').replace('.', '').replace(',', '')[:20]
    
    # Generate a concise summary of components for the main prompt
    component_summaries = []
    for name, code in all_components.items():
        summary = f"- {name} Component (Length: {len(code)} characters)"
        component_summaries.append(summary)
    
    component_names_found = list(all_components.keys())

    return f"""Combine the following HTML components into ONE complete HTML document.

BUSINESS: {business_name} ({business_category} - {business_sub_category})
- Business Size: {business_size}
- About Business: {about_business}
- Services: {chr(10).join(f"  • {s}" for s in services_list) if services_list else "Not specified"}
- Address: {address}
- Email: {email}
- Phone: {phone}
- Social Media: Facebook={facebook}, Instagram={instagram}, LinkedIn={linkedin}, Twitter={twitter}
- Extra Instructions: {extra_prompt}
Company Slug (for navigation IDs): {company_slug}
Theme Color: {theme_color}
Font: {font_name}
{f"Logo: {logo_url}" if logo_url else ""} (CRITICAL: Embed this logo in the navigation bar with appropriate sizing and alt text)
{f"Favicon: {favicon_url}" if favicon_url else ""} (CRITICAL: Embed this favicon in the <head> section)
Images: {', '.join(image_urls) if image_urls else 'None'}

COMPONENTS TO COMBINE (Refer to individual component HTML provided in separate messages):
{chr(10).join(component_summaries)}

CRITICAL: ALL {len(all_components)} components listed above MUST be included in the final HTML. Check each component section and copy its complete HTML code.

REQUIREMENTS:
1. Create complete HTML document: <!DOCTYPE html>, <html>, <head>, <body>, </html>
2. Include Bootstrap 5.3 CDN in <head>:
   <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
   <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
3. Include Google Fonts for {font_name} in <head>
4. Include ALL {len(all_components)} component HTML code in the EXACT ORDER they were provided as separate messages:
   - First: Navigation component (MUST BE INCLUDED)
   - Second: Hero component (MUST BE INCLUDED, add id="{company_slug}-home" to main section)
   - Third through Sixth: Dynamic components (MUST BE INCLUDED, in the order they appear above, add appropriate IDs like id="{company_slug}-about", id="{company_slug}-services", etc.)
   - Seventh: Contact component (MUST BE INCLUDED - CRITICAL, add id="{company_slug}-contact" to main section)
   - Eighth: Footer component (MUST BE INCLUDED - CRITICAL)
   
   CRITICAL: You MUST include exactly 8 components total:
   1. Navigation
   2. Hero
   3-6. Four dynamic components (check component names above)
   7. Contact (REQUIRED - must be included)
   8. Footer (REQUIRED - must be included)
   
   If Contact or Footer components are missing from the components list above, you MUST still create them or find them.
5. Add inline CSS in <style> tag for:
   - Theme color {theme_color} as primary color
   - Light shades: 20% lighter, 40% lighter of {theme_color}
   - Dark shades: 20% darker, 40% darker of {theme_color}
   - Apply theme color shades to buttons, links, backgrounds, accents
   - Smooth scrolling: html {{ scroll-behavior: smooth; }}
   - Animations and transitions
   - Consistent spacing: Each section should have minimum 80px padding-top and 80px padding-bottom (py-5 or py-5 class, or style="padding-top: 80px; padding-bottom: 80px;")
   - Full-width overrides for WordPress
   - Ensure proper spacing between ALL components (no components should be touching)
6. Add inline JavaScript in <script> tag before </body> for:
   - Navigation link handling (🚨 CRITICAL - must work in preview AND WordPress 🚨):
     * Company slug: {company_slug}
     * All anchor links (#{company_slug}-*) should scroll smoothly to target sections
     * Handle clicks on ALL navigation links (both in preview and WordPress):
       document.addEventListener('DOMContentLoaded', function() {{
         // Handle all anchor links with company slug format: #{company_slug}-home, #{company_slug}-about, etc.
         document.querySelectorAll('a[href^="#"]').forEach(function(link) {{
           link.addEventListener('click', function(e) {{
             const href = this.getAttribute('href');
             if (href && href.startsWith('#')) {{
               const targetId = href.substring(1);
               const target = document.getElementById(targetId);
               if (target) {{
                 e.preventDefault();
                 e.stopPropagation();
                 target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                 // Update URL hash without triggering scroll
                 if (history.pushState) {{
                   history.pushState(null, null, '#' + targetId);
                 }}
               }}
             }}
           }});
         }});
       }});
     * Also handle navigation on window load for dynamically loaded content
   - Contact form mailto: functionality (if not already in component)
   - Form validation
   - Scroll to top on load: window.scrollTo(0, 0)
7. CRITICAL SPACING: Ensure proper spacing between ALL components:
   - Each component section must have minimum 80px padding-top and 80px padding-bottom
   - Use Bootstrap classes: py-5 (80px) or py-5 (96px) for sections
   - Or inline style: style="padding-top: 80px; padding-bottom: 80px;"
   - NO components should be touching - there must be visible spacing between each
8. Use theme color {theme_color} and its shades consistently throughout ALL components
9. Make responsive using Bootstrap grid system
10. Include proper meta tags in <head> (viewport, charset, etc.)
11. Ensure all components maintain their inline CSS from individual generation

🚨 CRITICAL NAVIGATION & ID FORMAT 🚨:
12. Navigation links format (MANDATORY):
    - Company slug: {company_slug}
    - ALL navigation links MUST use format: #{company_slug}-home, #{company_slug}-about, #{company_slug}-services, #{company_slug}-contact
    - Example for navigation bar: <a href="#{company_slug}-home">Home</a>, <a href="#{company_slug}-about">About</a>, <a href="#{company_slug}-services">Services</a>, <a href="#{company_slug}-contact">Contact</a>
    - ❌ NEVER use: /home, /about, #home, #about
    - ✅ ALWAYS use: #{company_slug}-home, #{company_slug}-about, #{company_slug}-services, #{company_slug}-contact
    
13. Section IDs (MANDATORY - must match navigation links):
    - Hero section: id="{company_slug}-home"
    - About section: id="{company_slug}-about"
    - Services section: id="{company_slug}-services"
    - Contact section: id="{company_slug}-contact"
    - Other sections: id="{company_slug}-[section-name-lowercase]"
    - Example: <section id="{company_slug}-home" class="...">...</section>

CRITICAL VERIFICATION CHECKLIST (VERIFY ALL 8 COMPONENTS):
- [ ] All {len(all_components)} components are included (check each component section above) - VERIFY EACH COMPONENT BY NAME: {', '.join(component_names_found)}
- [ ] Navigation component is first with proper logo sizing (height: 40-50px) and company name visible (font-size: 18-24px)
- [ ] Hero component is second with id="{company_slug}-home"
- [ ] All 4 dynamic components are included in order (check each dynamic component name from planning)
- [ ] Contact component is included (REQUIRED - 7th component) with id="{company_slug}-contact" - IF MISSING, CREATE IT
- [ ] Footer component is included (REQUIRED - 8th component) - IF MISSING, CREATE IT
- [ ] Total count: Exactly 8 components (Navigation, Hero, 4 dynamic, Contact, Footer)
- [ ] Each section has minimum 80px padding top and bottom
- [ ] All navigation links use #{company_slug}-* format (e.g., #{company_slug}-home, #{company_slug}-about, #{company_slug}-contact)
- [ ] All sections have matching IDs for navigation links
- [ ] JavaScript handles anchor link scrolling (works in preview AND WordPress)
- [ ] All components have different visual styles (no repetition)
- [ ] Images are properly sized and integrated into components

CRITICAL: 
- Copy the ACTUAL HTML code from each component section above
- DO NOT use placeholders like "[Navigation Component]"
- Include the complete HTML code from each component
- Ensure all components are properly combined with consistent styling and proper spacing
- Verify ALL {len(all_components)} components are in the final HTML
- MANDATORY: You MUST include Contact component (7th) and Footer component (8th) - if they are not in the components list above, you MUST create them or search for them in the component sections
- Total components in final HTML MUST be exactly 8: Navigation, Hero, 4 dynamic components, Contact, Footer

COMPONENT COUNT VERIFICATION:
Before outputting final HTML, count the components:
1. Navigation ✓
2. Hero ✓
3. Dynamic Component 1 ✓
4. Dynamic Component 2 ✓
5. Dynamic Component 3 ✓
6. Dynamic Component 4 ✓
7. Contact ✓ (REQUIRED - must be present)
8. Footer ✓ (REQUIRED - must be present)

If Contact or Footer are missing, you MUST include them. Check the component sections above for "Contact" and "Footer" components.

Output ONLY the complete HTML code starting with <!DOCTYPE html> and ending with </html>. No markdown, no explanations."""