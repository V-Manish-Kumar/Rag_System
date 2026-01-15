"""
Vercel serverless function entry point.
Wraps the FastAPI app for Vercel's Python runtime.
"""

import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app

# Vercel expects a 'app' or 'handler' variable
handler = app
