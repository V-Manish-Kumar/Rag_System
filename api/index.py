"""
Vercel serverless function entry point.
Wraps the FastAPI app for Vercel's Python runtime.
"""

import sys
import os

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set environment to avoid .env file issues
os.environ.setdefault('PYTHONUNBUFFERED', '1')

try:
    # Import the FastAPI app
    from main import app
    
    # Export for Vercel
    handler = app
    
except Exception as e:
    # Fallback error handler
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI()
    
    @app.get("/")
    @app.get("/health")
    async def error_handler():
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to initialize application",
                "details": str(e),
                "backend_path": backend_path,
                "sys_path": sys.path[:3]
            }
        )
    
    handler = app
