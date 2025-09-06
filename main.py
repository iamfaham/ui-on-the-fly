from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os
import random
import asyncio
from dotenv import load_dotenv
from typing import List, Dict
import logging
import time
from collections import defaultdict
import redis
import json
from sqlalchemy import create_engine, Column, String, Float, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Dynamic UI Generator",
    description="An app that generates new LLM-created UIs on every request",
    version="1.0.0",
)


# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str
    model: str = "qwen-3-coder-480b"
    temperature: float = 0.8


class GenerateResponse(BaseModel):
    html: str
    prompt: str
    model: str


# Configuration
CEREBRAS_API_KEY = os.getenv("CEREBRAS_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

if not CEREBRAS_API_KEY:
    logger.warning("CEREBRAS_API_KEY not found in environment variables")

# Database setup for rate limiting
Base = declarative_base()
db_engine = None
SessionLocal = None


class RateLimitRecord(Base):
    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True, index=True)
    client_ip = Column(String, index=True)
    timestamp = Column(Float, index=True)

    __table_args__ = (Index("idx_client_timestamp", "client_ip", "timestamp"),)


# Initialize database connection
if DATABASE_URL:
    try:
        db_engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        # Create tables
        Base.metadata.create_all(bind=db_engine)
        logger.info("Connected to database successfully")
    except Exception as e:
        logger.warning(f"Failed to connect to database: {e}")
        db_engine = None
        SessionLocal = None

# Initialize Redis connection
redis_client = None
if REDIS_URL:
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        redis_client.ping()
        logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.warning(
            f"Failed to connect to Redis: {e}. Falling back to database or in-memory rate limiting."
        )
        redis_client = None
else:
    logger.warning("REDIS_URL not found. Using database or in-memory rate limiting")

# UI generation prompts
UI_PROMPTS = [
    "Create a beautiful landing page for a coffee shop with warm colors and cozy atmosphere",
    "Design a modern portfolio website for a photographer with stunning gallery layout",
    "Build a sleek dashboard interface for a fitness tracking app with charts and metrics",
    "Create a minimalist blog homepage with dark theme and elegant typography",
    "Design a product showcase page for eco-friendly products with green theme",
    "Build a creative agency homepage with bold typography and animated elements",
    "Create a weather app interface with animated weather icons and gradients",
    "Design a music player interface with vinyl record aesthetic and controls",
    "Build a cryptocurrency dashboard with real-time charts and modern design",
    "Create a food delivery app interface with appetizing food images",
    "Design a travel booking website with beautiful destination photos",
    "Build a social media dashboard with card-based layout and interactions",
    "Create a gaming website with neon colors and futuristic design",
    "Design a meditation app interface with calming colors and zen elements",
    "Build a real estate website with property listings and modern layout",
]

# Available models
AVAILABLE_MODELS = ["qwen-3-coder-480b", "gpt-oss-120b"]

# In-memory storage for UI history
ui_history: List[Dict] = []

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # 60 seconds

# Fallback in-memory storage (used when Redis is not available)
rate_limit_storage = defaultdict(list)


def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit using Redis, database, or in-memory fallback"""
    current_time = time.time()

    if redis_client:
        return check_rate_limit_redis(client_ip, current_time)
    elif SessionLocal:
        return check_rate_limit_database(client_ip, current_time)
    else:
        return check_rate_limit_memory(client_ip, current_time)


def check_rate_limit_redis(client_ip: str, current_time: float) -> bool:
    """Redis-based rate limiting"""
    try:
        key = f"rate_limit:{client_ip}"

        # Use Redis pipeline for atomic operations
        pipe = redis_client.pipeline()

        # Remove expired entries
        pipe.zremrangebyscore(key, 0, current_time - RATE_LIMIT_WINDOW)

        # Count current requests
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(current_time): current_time})

        # Set expiration for the key
        pipe.expire(key, RATE_LIMIT_WINDOW)

        # Execute pipeline
        results = pipe.execute()
        current_count = results[1]  # Result of zcard

        return current_count < RATE_LIMIT_REQUESTS

    except Exception as e:
        logger.error(f"Redis rate limiting error: {e}. Falling back to in-memory.")
        return check_rate_limit_memory(client_ip, current_time)


def check_rate_limit_database(client_ip: str, current_time: float) -> bool:
    """Database-based rate limiting"""
    try:
        db = SessionLocal()
        try:
            # Clean old records outside the window
            cutoff_time = current_time - RATE_LIMIT_WINDOW
            db.query(RateLimitRecord).filter(
                RateLimitRecord.client_ip == client_ip,
                RateLimitRecord.timestamp < cutoff_time,
            ).delete()

            # Count current requests
            current_count = (
                db.query(RateLimitRecord)
                .filter(RateLimitRecord.client_ip == client_ip)
                .count()
            )

            # Check if under limit
            if current_count >= RATE_LIMIT_REQUESTS:
                return False

            # Add current request
            new_record = RateLimitRecord(client_ip=client_ip, timestamp=current_time)
            db.add(new_record)
            db.commit()

            return True

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Database rate limiting error: {e}. Falling back to in-memory.")
        return check_rate_limit_memory(client_ip, current_time)


def check_rate_limit_memory(client_ip: str, current_time: float) -> bool:
    """In-memory rate limiting (fallback)"""
    # Clean old requests outside the window
    rate_limit_storage[client_ip] = [
        req_time
        for req_time in rate_limit_storage[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]

    # Check if under limit
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False

    # Add current request
    rate_limit_storage[client_ip].append(current_time)
    return True


def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    # Check for forwarded IP first (for proxies/load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"


async def call_cerebras_api(
    prompt: str, model: str = "qwen-3-coder-480b", temperature: float = 0.8
) -> str:
    """Call Cerebras API to generate UI code"""

    system_prompt = """You are an expert web developer and UI/UX designer. Create a complete, beautiful HTML page based on the user's request.

Requirements:
- Create a single HTML file with embedded CSS and JavaScript
- Use modern CSS features (flexbox, grid, animations, gradients)
- Make it fully responsive and mobile-friendly
- Include interactive elements and hover effects
- Use beautiful color schemes and typography
- Add subtle animations and transitions
- Use CDN links for any external resources (fonts, icons)
- Ensure the design is visually striking and professional
- Include proper semantic HTML structure
- Make it accessible with proper contrast and ARIA labels
- Return ONLY the complete HTML code, no explanations or markdown

The page should be production-ready and visually impressive!"""

    try:
        from cerebras.cloud.sdk import Cerebras

        client = Cerebras(api_key=CEREBRAS_API_KEY)

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            model=model,
            temperature=temperature,
            max_tokens=4000,
        )

        generated_content = chat_completion.choices[0].message.content

        # Clean up the response (remove markdown code blocks if present)
        clean_html = generated_content.replace("```html", "").replace("```", "").strip()

        logger.info(f"Successfully generated UI with {len(clean_html)} characters")
        return clean_html

    except Exception as e:
        logger.error(f"Error calling Cerebras API: {e}")
        raise HTTPException(status_code=503, detail="Failed to generate UI")


def get_fallback_ui(error_msg: str = "Something went wrong") -> str:
    """Generate a simple fallback UI when API fails"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oops!</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            text-align: center;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            padding: 4rem 3rem;
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.2);
            max-width: 500px;
            width: 90%;
        }
        
        .emoji {
            font-size: 4rem;
            margin-bottom: 1.5rem;
            animation: bounce 2s infinite;
        }
        
        h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        p {
            font-size: 1.1rem;
            margin-bottom: 2rem;
            opacity: 0.9;
            line-height: 1.5;
        }
        
        .retry-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
            padding: 12px 30px;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .retry-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            border-color: rgba(255, 255, 255, 0.5);
            transform: translateY(-2px);
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% {
                transform: translateY(0);
            }
            40% {
                transform: translateY(-10px);
            }
            60% {
                transform: translateY(-5px);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="emoji">🙈</div>
        <h1>Oops!</h1>
        <p>Something went wrong, but don't worry - it happens to the best of us!</p>
        <button class="retry-btn" onclick="location.reload()">
            Try Again
        </button>
    </div>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def generate_random_ui(request: Request):
    """Generate a random UI on each request"""
    # Check rate limit
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
        )

    try:
        # Select a random prompt
        random_prompt = random.choice(UI_PROMPTS)
        random_model = random.choice(AVAILABLE_MODELS)

        logger.info(f"Generating UI with prompt: {random_prompt}")

        # Generate UI using Cerebras API
        html_content = await call_cerebras_api(random_prompt, random_model)

        # Store in history
        ui_entry = {
            "prompt": random_prompt,
            "model": random_model,
            "html_length": len(html_content),
            "timestamp": asyncio.get_event_loop().time(),
        }
        ui_history.append(ui_entry)

        # Keep only last 20 entries
        if len(ui_history) > 20:
            ui_history.pop(0)

        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Error generating UI: {e}")
        return HTMLResponse(content=get_fallback_ui("API temporarily unavailable"))


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_custom_ui(request: GenerateRequest, http_request: Request):
    """Generate UI with custom prompt"""
    # Check rate limit
    client_ip = get_client_ip(http_request)
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
        )

    try:
        if not request.prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty")

        if request.model not in AVAILABLE_MODELS:
            raise HTTPException(
                status_code=400, detail=f"Model must be one of: {AVAILABLE_MODELS}"
            )

        logger.info(f"Generating custom UI: {request.prompt[:50]}...")

        html_content = await call_cerebras_api(
            request.prompt, request.model, request.temperature
        )

        # Store in history
        ui_entry = {
            "prompt": request.prompt,
            "model": request.model,
            "html_length": len(html_content),
            "timestamp": asyncio.get_event_loop().time(),
        }
        ui_history.append(ui_entry)

        return GenerateResponse(
            html=html_content, prompt=request.prompt, model=request.model
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating custom UI: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate UI")


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    """Simple admin panel for custom UI generation"""
    admin_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI Generator Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 2rem;
            color: #e2e8f0;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border: 1px solid rgba(148, 163, 184, 0.1);
        }
        
        h1 {
            text-align: center;
            margin-bottom: 2rem;
            color: #60a5fa;
            font-size: 2.5rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #cbd5e1;
        }
        
        textarea, select, input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #475569;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s;
            background: rgba(51, 65, 85, 0.8);
            color: #e2e8f0;
        }
        
        textarea {
            min-height: 120px;
            resize: vertical;
        }
        
        textarea:focus, select:focus, input:focus {
            outline: none;
            border-color: #60a5fa;
            background: rgba(51, 65, 85, 1);
        }
        
        textarea::placeholder {
            color: #94a3b8;
        }
        
        .btn {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            border: none;
            padding: 1rem 2rem;
            border-radius: 10px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
            margin-top: 1rem;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
            background: linear-gradient(135deg, #2563eb, #1e40af);
        }
        
        .result {
            margin-top: 2rem;
            padding: 1rem;
            background: rgba(30, 58, 138, 0.2);
            border-radius: 10px;
            border-left: 4px solid #60a5fa;
            color: #e2e8f0;
        }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #94a3b8;
        }
        
        .spinner {
            border: 3px solid #374151;
            border-top: 3px solid #60a5fa;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .credit-overlay {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(30, 41, 59, 0.9);
            backdrop-filter: blur(10px);
            padding: 8px 16px;
            border-radius: 20px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            font-size: 0.9rem;
            color: #94a3b8;
            z-index: 1000;
            transition: all 0.3s ease;
        }
        
        .credit-overlay:hover {
            background: rgba(30, 41, 59, 1);
            border-color: rgba(148, 163, 184, 0.4);
            transform: translateY(-2px);
        }
        
        .credit-overlay a {
            color: #60a5fa;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.3s ease;
        }
        
        .credit-overlay a:hover {
            color: #93c5fd;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 UI Generator Admin</h1>
        
        <form id="generateForm">
            <div class="form-group">
                <label for="prompt">UI Description</label>
                <textarea 
                    id="prompt" 
                    name="prompt" 
                    placeholder="Describe the UI you want to generate..."
                    required
                ></textarea>
            </div>
            
            <div class="form-group">
                <label for="model">Model</label>
                <select id="model" name="model">
                    <option value="qwen-3-coder-480b">qwen-3-coder-480b</option>
                    <option value="gpt-oss-120b">gpt-oss-120b</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="temperature">Creativity (0.1 - 1.0)</label>
                <input type="number" id="temperature" name="temperature" min="0.1" max="1.0" step="0.1" value="0.8">
            </div>
            
            <button type="submit" class="btn">Generate UI</button>
        </form>
        
        <div id="result" style="display: none;"></div>
    </div>
    
    <div class="credit-overlay">
        Built by <a href="https://github.com/iamfaham" target="_blank" rel="noopener noreferrer">iamfaham</a>
    </div>
    
    <script>
        document.getElementById('generateForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const data = {
                prompt: formData.get('prompt'),
                model: formData.get('model'),
                temperature: parseFloat(formData.get('temperature'))
            };
            
            const result = document.getElementById('result');
            result.style.display = 'block';
            result.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Generating your custom UI...</p>
                </div>
            `;
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result_data = await response.json();
                
                result.innerHTML = `
                    <div class="result">
                        <h3>✅ Generated Successfully!</h3>
                        <p><strong>Prompt:</strong> ${result_data.prompt}</p>
                        <p><strong>Model:</strong> ${result_data.model}</p>
                        <p><strong>HTML Size:</strong> ${result_data.html.length} characters</p>
                        <div style="margin-top: 1rem;">
                            <h4>Preview:</h4>
                            <iframe 
                                srcdoc="${result_data.html.replace(/"/g, '&quot;')}" 
                                style="width: 100%; height: 600px; border: 2px solid #e5e7eb; border-radius: 10px; margin-top: 0.5rem;"
                                title="Generated UI Preview">
                            </iframe>
                        </div>
                        <p style="margin-top: 1rem;"><a href="/" target="_blank">Open Main Generator</a> to see random UIs</p>
                    </div>
                `;
                
            } catch (error) {
                result.innerHTML = `
                    <div class="result" style="background: #fef2f2; border-color: #f87171;">
                        <h3>❌ Error</h3>
                        <p>Failed to generate UI: ${error.message}</p>
                    </div>
                `;
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=admin_html)


@app.get("/api/history")
async def get_ui_history(request: Request):
    """Get UI generation history"""
    # Check rate limit
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
        )

    return {"history": ui_history[-10:], "total": len(ui_history)}


@app.get("/api/models")
async def get_available_models(request: Request):
    """Get list of available models"""
    # Check rate limit
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
        )

    return {"models": AVAILABLE_MODELS}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_status = "not_available"
    if redis_client:
        try:
            redis_client.ping()
            redis_status = "connected"
        except:
            redis_status = "disconnected"

    db_status = "not_available"
    if SessionLocal:
        try:
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            db_status = "connected"
        except:
            db_status = "disconnected"

    # Determine which storage is being used
    if redis_client and redis_status == "connected":
        storage_type = "redis"
    elif SessionLocal and db_status == "connected":
        storage_type = "database"
    else:
        storage_type = "memory"

    return {
        "status": "healthy",
        "api_key_configured": bool(CEREBRAS_API_KEY),
        "total_generated": len(ui_history),
        "rate_limiting": {
            "redis_status": redis_status,
            "database_status": db_status,
            "requests_per_window": RATE_LIMIT_REQUESTS,
            "window_seconds": RATE_LIMIT_WINDOW,
            "storage_type": storage_type,
        },
    }


@app.get("/api/random-prompt")
async def get_random_prompt(request: Request):
    """Get a random UI generation prompt"""
    # Check rate limit
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds.",
        )

    return {"prompt": random.choice(UI_PROMPTS)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
