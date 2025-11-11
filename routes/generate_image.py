"""Route for Gemini image generation"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
from datetime import datetime
import time # Import time for delays
from utils.api_keys import _key_manager, is_rate_limit_error_openai, get_openai_key, rotate_openai_key # Import new OpenAI key functions


router = APIRouter()

@router.post("/generate_image")
async def generate_image(request: Request):
    """
    Generate images using Google Gemini (gemini-2.0-flash-exp-image-generation)
    Input: { "prompt": "image description" }
    Output: { "images": ["url1", "url2", ...] }
    """
    try:
        data = await request.json()
        prompt = data.get('prompt', '')
        print(f"[LOG] Received image generation prompt: {prompt}")
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        max_retries = 2 # Initial attempt + 1 retry = 2 attempts total
        retry_delay = 5 # seconds
        
        # Use _key_manager to get and rotate keys
        if _key_manager is None:
            # This should be initialized at startup, but for safety
            from utils.api_keys import _key_manager as init_key_manager
            _ = init_key_manager # Access to initialize it

        for attempt in range(max_retries):
            gemini_key = _key_manager.get_key() if _key_manager else None
            if not gemini_key:
                raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured or no keys available.")

            try:
                print(f"[LOG] Image generation attempt {attempt + 1}/{max_retries} for prompt: {prompt[:50]}...")
                client = genai.Client(api_key=gemini_key)
                print("[LOG] Calling Gemini Image API (generate_content)...")
                # Generate mixed content (text + images)
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp-image-generation",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=['Text', 'Image']
                    )
                )
                
                # If successful, break the retry loop
                # Save images and collect URLs
                image_urls = []
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs('static/generated', exist_ok=True)
                # Iterate over parts and save any images
                parts = []
                try:
                    parts = response.candidates[0].content.parts
                except Exception:
                    parts = []
                img_idx = 0
                for part in parts:
                    inline = getattr(part, 'inline_data', None)
                    if inline and getattr(inline, 'data', None):
                        try:
                            img_bytes = inline.data
                            image = Image.open(BytesIO(img_bytes))
                            filename = f"image_{timestamp}_{img_idx}.png"
                            image_path = f"static/generated/{filename}"
                            image.save(image_path)
                            image_urls.append(f"/static/generated/{filename}")
                            img_idx += 1
                        except Exception as save_err:
                            print(f"[WARN] Failed saving one image: {save_err}")
                print(f"[LOG] {len(image_urls)} images generated successfully")
                return JSONResponse({
                    "images": image_urls,
                    "success": True
                })
            except Exception as e:
                print(f"[WARN] Image generation attempt {attempt + 1}/{max_retries} failed for {prompt[:50]}...: {e}")
                if _key_manager and _key_manager.is_rate_limit_error(e):
                    print("[LOG] Rate limit detected, rotating to next key...")
                    if _key_manager.rotate_key():
                        time.sleep(retry_delay)
                        continue # Try again with the new key
                    else:
                        print("[WARN] No more keys to rotate, exhausting retries.")
                # If not a rate limit error, or no more keys to rotate, re-raise for immediate failure
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=500, detail=f"Failed to generate image after {max_retries} attempts: {str(e)}")
                else:
                    # For non-rate-limit errors, or if rotation failed, fail immediately
                    raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"[ERROR] Error in generate_image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

