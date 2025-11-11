import os
from dotenv import load_dotenv

load_dotenv()

# print(f"[DEBUG] Environment variables after load_dotenv():\n  GEMINI_API_KEY = {os.getenv('GEMINI_API_KEY')}\n  GEMINI_API_KEYS = {os.getenv('GEMINI_API_KEYS')}\n  OPENROUTER_API_KEY = {os.getenv('OPENROUTER_API_KEY')}") # Added for debugging

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Import StaticFiles

from routes.generate_code import router as generate_code_router
from routes.generate_image import router as generate_image_router

app = FastAPI(title="AI Website Builder Backend")

# Middleware to add Cross-Origin-Resource-Policy header
@app.middleware("http")
async def add_cross_origin_resource_policy_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

# CORS setup
# Allowing all origins for development to avoid issues with file:// frontend
origins = [os.getenv("FRONTEND_URL", "http://localhost:5173")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] , # Always allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Remove the default StaticFiles mount
# app.mount("/static", StaticFiles(directory="static"), name="static")

from fastapi.responses import FileResponse # Import FileResponse

@app.get("/static/{filepath:path}")
async def serve_static(filepath: str):
    file_path = os.path.join("static", filepath)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    response = FileResponse(file_path)
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    return response

# Ensure the static/generated directory exists
os.makedirs('static/generated', exist_ok=True)

@app.get("/")
async def index():
    return {
        "status": "running",
        "message": "AI Website Builder Backend API",
        "endpoints": {
            "/edit_component": "POST - Edit React component with AI",
            "/generate_image": "POST - Generate images with Gemini"
        }
    }

# Remove the custom serve_generated_image route as StaticFiles handles it
# @app.get("/static/generated/{filename:path}")
# async def serve_generated_image(filename: str):
#     image_path = os.path.join("static", "generated", filename)
#     if not os.path.exists(image_path):
#         raise HTTPException(status_code=404, detail="File not found")
#     headers = {
#         "Access-Control-Allow-Origin": "*",
#         "Access-Control-Allow-Methods": "GET, OPTIONS",
#         "Access-Control-Allow-Headers": "Content-Type",
#         "Cache-Control": "public, max-age=300",
#         "Content-Type": "image/png"
#     }
#     return FileResponse(image_path, headers=headers)

app.include_router(generate_code_router)
app.include_router(generate_image_router)
