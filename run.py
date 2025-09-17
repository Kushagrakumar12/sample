#!/usr/bin/env python3
"""
AI-Powered Train Traffic Control System
Main entry point for running the application
"""

import uvicorn
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    print("🚆 Starting AI-Powered Train Traffic Control System...")
    print("=" * 60)
    print("Backend API will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("WebSocket endpoint: ws://localhost:8000/ws/{client_id}")
    print("=" * 60)
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )