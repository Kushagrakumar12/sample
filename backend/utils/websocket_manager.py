"""
WebSocket connection manager for real-time updates
"""

from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio
from datetime import datetime

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_info: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_info[client_id] = {
            "connected_at": datetime.now(),
            "client_id": client_id
        }
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection",
            "message": f"Connected as {client_id}",
            "timestamp": datetime.now().isoformat()
        }, client_id)
        
        print(f"🔗 WebSocket client {client_id} connected")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_info:
            del self.client_info[client_id]
        print(f"❌ WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected_clients = []
        
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message_json)
            except Exception as e:
                print(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def send_train_update(self, train_data: dict):
        """Send train position/status update to all clients"""
        message = {
            "type": "train_update",
            "data": train_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def send_schedule_update(self, schedule_data: dict):
        """Send schedule update to all clients"""
        message = {
            "type": "schedule_update",
            "data": schedule_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def send_conflict_alert(self, conflict_data: dict):
        """Send conflict alert to all clients"""
        message = {
            "type": "conflict_alert",
            "data": conflict_data,
            "timestamp": datetime.now().isoformat(),
            "priority": conflict_data.get("severity", "medium")
        }
        await self.broadcast(message)
    
    async def send_optimization_result(self, result_data: dict):
        """Send optimization result to all clients"""
        message = {
            "type": "optimization_result",
            "data": result_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    def get_connected_clients(self) -> List[Dict]:
        """Get list of connected clients"""
        return [
            {
                "client_id": client_id,
                "connected_at": info["connected_at"].isoformat()
            }
            for client_id, info in self.client_info.items()
        ]
    
    async def ping_clients(self):
        """Send ping to all clients to check connection health"""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(ping_message)

# Background task to simulate real-time updates
class RealTimeUpdater:
    """Handles real-time data updates and notifications"""
    
    def __init__(self, websocket_manager: WebSocketManager, db_session):
        self.ws_manager = websocket_manager
        self.db = db_session
        self.is_running = False
    
    async def start_updates(self):
        """Start the real-time update loop"""
        self.is_running = True
        while self.is_running:
            try:
                # Simulate train position updates
                await self._update_train_positions()
                
                # Check for new conflicts
                await self._check_conflicts()
                
                # Send periodic status updates
                await self._send_system_status()
                
                # Wait before next update
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                print(f"Error in real-time updater: {e}")
                await asyncio.sleep(5)
    
    def stop_updates(self):
        """Stop the real-time update loop"""
        self.is_running = False
    
    async def _update_train_positions(self):
        """Simulate train position updates"""
        # This would normally get real data from GPS/sensors
        # For demo, we'll create simulated updates
        
        from ..models.database import TrainMovement, Train
        
        # Get some active trains
        active_trains = self.db.query(Train).filter(Train.is_active == True).limit(3).all()
        
        for train in active_trains:
            # Simulate position update
            simulated_position = {
                "train_id": train.id,
                "train_number": train.number,
                "current_position_km": float(hash(str(datetime.now())[:16]) % 100),
                "current_speed_kmh": float(hash(str(datetime.now())[:15]) % 120),
                "direction": "north",
                "track_id": 1,  # Simplified
                "timestamp": datetime.now().isoformat()
            }
            
            await self.ws_manager.send_train_update(simulated_position)
    
    async def _check_conflicts(self):
        """Check for new conflicts and send alerts"""
        # This would normally run the conflict detection algorithm
        # For demo, we'll occasionally send a mock conflict
        
        import random
        if random.random() < 0.1:  # 10% chance of conflict alert
            mock_conflict = {
                "train1_id": 1,
                "train2_id": 2,
                "track_id": 1,
                "severity": "medium",
                "message": "Potential scheduling conflict detected",
                "resolution": "Adjust departure time by 15 minutes"
            }
            
            await self.ws_manager.send_conflict_alert(mock_conflict)
    
    async def _send_system_status(self):
        """Send periodic system status updates"""
        status = {
            "active_trains": 5,  # Would get from database
            "on_time_percentage": 87.5,
            "active_conflicts": 1,
            "system_health": "operational",
            "last_optimization": datetime.now().isoformat()
        }
        
        message = {
            "type": "system_status",
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.ws_manager.broadcast(message)