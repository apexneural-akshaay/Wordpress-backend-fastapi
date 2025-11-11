# AI Website Builder - Backend

Flask-based backend API for the AI Website Builder application.

## Features

- **Code Generation**: Uses Gemini LLM to generate and edit HTML websites using Bootstrap documentation as reference
- **Image Generation**: Uses Google Gemini (gemini-2.0-flash-exp-image-generation) to generate images from text prompts
- **CORS Enabled**: Ready for cross-origin requests from frontend

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the backend directory:

```bash
# OpenRouter no longer used - using Gemini LLM instead
# GEMINI_API_KEY is required for website generation
GEMINI_API_KEY=your_gemini_key_here
```

### 5. Run the Server

```bash
python app.py
```

Server will start at `http://localhost:5000`

## API Endpoints

### POST /edit_component

Edit a React component using AI.

**Request Body:**
```json
{
  "prompt": "Add a blue button that says Click Me",
  "currentCode": "export default function EditablePage() { ... }"
}
```

**Response:**
```json
{
  "code": "export default function EditablePage() { ... }",
  "success": true
}
```

### POST /generate_image

Generate images using Gemini AI.

**Request Body:**
```json
{
  "prompt": "A robot holding a red skateboard"
}
```

**Response:**
```json
{
  "images": [
    "/static/generated/image_20241013_120000_0.png",
    "/static/generated/image_20241013_120000_1.png",
    "/static/generated/image_20241013_120000_2.png",
    "/static/generated/image_20241013_120000_3.png"
  ],
  "success": true
}
```

## Project Structure

```
backend/
├── app.py                  # Main Flask application
├── routes/
│   ├── __init__.py
│   ├── generate_code.py    # Code generation route
│   └── generate_image.py   # Image generation route
├── utils/
│   ├── prompts.py          # AI system prompts
│   └── constants.py        # Configuration constants
├── static/
│   └── generated/          # Generated images storage
├── requirements.txt
├── .env.example
└── README.md
```

## Logs

The application logs all major actions to the console:
- `[LOG] Received user edit prompt`
- `[LOG] Calling AI model...`
- `[LOG] AI returned JSX component successfully`
- `[LOG] Calling Gemini Image API (generate_content)...`
- `[LOG] N images generated successfully`
- `[ERROR] ...` for any errors

## Notes

- Generated images are stored in `static/generated/`
- Images are named with timestamps to avoid conflicts
- The API uses Claude 3.5 Sonnet for code generation
- Image generation creates 4 variations per prompt

