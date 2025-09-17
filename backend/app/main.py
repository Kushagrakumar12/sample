"""
AI-Powered Precise Train Traffic Control System
Main FastAPI application entry point
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
from typing import List

from .api import trains, tracks, schedules, optimization
from .models.database import engine, Base
from .utils.websocket_manager import WebSocketManager

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AI Train Traffic Control System",
    description="Comprehensive AI-powered decision-support system for railway operations",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket manager for real-time updates
ws_manager = WebSocketManager()

# Include API routers
app.include_router(trains.router, prefix="/api/trains", tags=["trains"])
app.include_router(tracks.router, prefix="/api/tracks", tags=["tracks"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["schedules"])
app.include_router(optimization.router, prefix="/api/optimization", tags=["optimization"])

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "AI-Powered Train Traffic Control System",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "System operational"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo message back for testing
            await ws_manager.send_personal_message(json.loads(data), client_id)
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    print("🚆 AI Train Traffic Control System starting up...")
    print("📊 Database connections established")
    print("🔗 WebSocket manager initialized")
    print("✅ System ready for operations")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )