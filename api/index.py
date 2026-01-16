"""
Vercel serverless function entry point.
Wraps the FastAPI app for Vercel's Python runtime.
This handles ALL /api/* routes through FastAPI.
"""

import sys
import os

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set environment
os.environ.setdefault('PYTHONUNBUFFERED', '1')

try:
    # Import the FastAPI app
    from main import app
    
    # Create ASGI handler for Vercel
    # Vercel will route /api/* to this function
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
    
    # Vercel expects 'app' or 'handler' to be exported
    # Export both for compatibility
    __all__ = ['handler', 'app']
    
except ImportError as ie:
    # Mangum not installed, try direct export
    try:
        from main import app
        handler = app
        __all__ = ['handler', 'app']
    except Exception as e:
        # Fallback error handler
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        app = FastAPI()
        
        @app.get("/{path:path}")
        @app.post("/{path:path}")
        async def error_handler(path: str):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Failed to initialize application",
                    "details": str(e),
                    "import_error": str(ie) if 'ie' in locals() else None,
                    "path": path,
                    "backend_path": backend_path,
                    "sys_path": sys.path
                }
            )
        
        handler = app
        __all__ = ['handler', 'app']
