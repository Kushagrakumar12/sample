"""
Module 1: Obstacle Detection & Classification

This module implements YOLOv8-based obstacle detection with simulated camera feed.
Detects and classifies various obstacles and estimates distances for real-time audio alerts.
"""

import cv2
import numpy as np
import threading
import time
from typing import Dict, List, Tuple, Optional
import json
import os
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    print("Warning: ultralytics not available. Using mock detection.")
    YOLO = None


class ObstacleDetector:
    """
    Real-time obstacle detection and classification system using YOLOv8.
    Provides distance estimation and object classification for navigation assistance.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the obstacle detector with configuration."""
        self.config = self._load_config(config_path)
        self.model = None
        self.camera = None
        self.is_running = False
        self.detection_thread = None
        self.current_detections = []
        self.detection_lock = threading.Lock()
        
        # Load class names
        self.class_names = self._load_class_names()
        
        # Initialize mock camera simulation
        self.mock_mode = True
        self.mock_frame_count = 0
        
        self._setup_model()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration settings."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "detection_settings": {
                "confidence_threshold": 0.5,
                "detection_classes": [
                    "person", "bicycle", "car", "motorcycle", "bus", "truck",
                    "traffic light", "stop sign", "bench", "fire hydrant"
                ],
                "alert_distances": {
                    "person": 1.5,
                    "vehicle": 3.0,
                    "stairs": 1.0,
                    "pothole": 0.8,
                    "overhead_obstacle": 1.2
                }
            }
        }
    
    def _load_class_names(self) -> List[str]:
        """Load YOLO class names."""
        try:
            class_names_path = Path(__file__).parent.parent / "models" / "class_names.txt"
            with open(class_names_path, 'r') as f:
                return [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            # Default COCO class names (subset)
            return [
                "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
                "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench"
            ]
    
    def _setup_model(self):
        """Initialize the YOLO model."""
        if YOLO is not None:
            try:
                # Try to load YOLOv8 model
                model_path = Path(__file__).parent.parent / "models" / "yolov8n.pt"
                if model_path.exists():
                    self.model = YOLO(str(model_path))
                else:
                    # Download default model
                    self.model = YOLO('yolov8n.pt')
                    print("Downloaded YOLOv8 nano model")
            except Exception as e:
                print(f"Failed to load YOLO model: {e}")
                self.model = None
                self.mock_mode = True
        else:
            print("Using mock detection mode - YOLO not available")
            self.mock_mode = True
    
    def start_detection(self, camera_id: int = 0, use_mock: bool = True):
        """Start the obstacle detection system."""
        if self.is_running:
            return
        
        self.is_running = True
        self.mock_mode = use_mock
        
        if not use_mock:
            try:
                self.camera = cv2.VideoCapture(camera_id)
                if not self.camera.isOpened():
                    print("Warning: Could not open camera. Using mock mode.")
                    self.mock_mode = True
            except Exception as e:
                print(f"Camera initialization failed: {e}. Using mock mode.")
                self.mock_mode = True
        
        # Start detection thread
        self.detection_thread = threading.Thread(target=self._detection_loop)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        
        print("Obstacle detection started")
    
    def stop_detection(self):
        """Stop the obstacle detection system."""
        self.is_running = False
        
        if self.detection_thread:
            self.detection_thread.join(timeout=2.0)
        
        if self.camera:
            self.camera.release()
        
        print("Obstacle detection stopped")
    
    def _detection_loop(self):
        """Main detection loop running in separate thread."""
        while self.is_running:
            try:
                frame = self._get_frame()
                if frame is not None:
                    detections = self._detect_objects(frame)
                    
                    with self.detection_lock:
                        self.current_detections = detections
                    
                    time.sleep(0.1)  # Limit to 10 FPS
                else:
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"Detection loop error: {e}")
                time.sleep(1.0)
    
    def _get_frame(self) -> Optional[np.ndarray]:
        """Get the current camera frame or generate mock frame."""
        if self.mock_mode:
            return self._generate_mock_frame()
        
        if self.camera and self.camera.isOpened():
            ret, frame = self.camera.read()
            if ret:
                return frame
        
        return None
    
    def _generate_mock_frame(self) -> np.ndarray:
        """Generate a mock camera frame for simulation."""
        self.mock_frame_count += 1
        
        # Create a 640x480 frame with some patterns
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some background patterns
        frame[:, :, 0] = 50  # Blue channel
        frame[:, :, 1] = 100  # Green channel
        frame[:, :, 2] = 150  # Red channel
        
        # Simulate moving objects
        t = self.mock_frame_count * 0.1
        
        # Moving person simulation
        person_x = int(320 + 200 * np.sin(t))
        person_y = 300
        cv2.rectangle(frame, (person_x-30, person_y-60), (person_x+30, person_y+60), (0, 255, 0), 2)
        cv2.putText(frame, "PERSON", (person_x-30, person_y-70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Static car simulation
        if self.mock_frame_count % 100 < 50:  # Appears intermittently
            car_x, car_y = 500, 350
            cv2.rectangle(frame, (car_x-50, car_y-25), (car_x+50, car_y+25), (255, 0, 0), 2)
            cv2.putText(frame, "CAR", (car_x-20, car_y-30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        return frame
    
    def _detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """Detect objects in the current frame."""
        if self.mock_mode or self.model is None:
            return self._mock_detection(frame)
        
        try:
            # Run YOLO detection
            results = self.model(frame, conf=self.config["detection_settings"]["confidence_threshold"])
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for i in range(len(boxes)):
                        x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
                        confidence = boxes.conf[i].cpu().numpy()
                        class_id = int(boxes.cls[i].cpu().numpy())
                        
                        if class_id < len(self.class_names):
                            class_name = self.class_names[class_id]
                            distance = self._estimate_distance(x1, y1, x2, y2, class_name)
                            
                            detection = {
                                "class": class_name,
                                "confidence": float(confidence),
                                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                                "distance": distance,
                                "center": [(x1 + x2) / 2, (y1 + y2) / 2]
                            }
                            detections.append(detection)
            
            return detections
            
        except Exception as e:
            print(f"Detection error: {e}")
            return self._mock_detection(frame)
    
    def _mock_detection(self, frame: np.ndarray) -> List[Dict]:
        """Generate mock detections for simulation."""
        detections = []
        t = self.mock_frame_count * 0.1
        
        # Mock person detection
        person_x = int(320 + 200 * np.sin(t))
        person_distance = 2.0 + 0.5 * np.sin(t * 2)
        
        detections.append({
            "class": "person",
            "confidence": 0.85,
            "bbox": [person_x-30, 240, person_x+30, 360],
            "distance": person_distance,
            "center": [person_x, 300]
        })
        
        # Mock car detection (intermittent)
        if self.mock_frame_count % 100 < 50:
            car_distance = 4.0 + 1.0 * np.sin(t * 0.5)
            detections.append({
                "class": "car",
                "confidence": 0.92,
                "bbox": [450, 325, 550, 375],
                "distance": car_distance,
                "center": [500, 350]
            })
        
        return detections
    
    def _estimate_distance(self, x1: float, y1: float, x2: float, y2: float, class_name: str) -> float:
        """Estimate distance to object based on bounding box size."""
        # Simple distance estimation based on bounding box height
        height = y2 - y1
        width = x2 - x1
        
        # Basic calibration values (would need real-world calibration)
        if class_name == "person":
            # Assume average person height is 1.7m
            estimated_distance = (1.7 * 480) / (height * 0.8)  # 480 is frame height
        elif class_name in ["car", "truck", "bus"]:
            # Assume average vehicle height is 1.5m
            estimated_distance = (1.5 * 480) / (height * 0.7)
        else:
            # General estimation
            estimated_distance = (1.0 * 480) / (height * 0.6)
        
        # Clamp distance to reasonable range
        return max(0.5, min(20.0, estimated_distance))
    
    def get_current_detections(self) -> List[Dict]:
        """Get the most recent detection results."""
        with self.detection_lock:
            return self.current_detections.copy()
    
    def get_priority_alerts(self) -> List[Dict]:
        """Get detections that require immediate alerts."""
        detections = self.get_current_detections()
        alerts = []
        
        alert_distances = self.config["detection_settings"]["alert_distances"]
        
        for detection in detections:
            class_name = detection["class"]
            distance = detection["distance"]
            
            # Check if object is within alert distance
            if class_name in alert_distances:
                alert_threshold = alert_distances[class_name]
            elif class_name in ["car", "truck", "bus", "motorcycle"]:
                alert_threshold = alert_distances.get("vehicle", 3.0)
            else:
                alert_threshold = 2.0  # Default threshold
            
            if distance <= alert_threshold:
                alert = detection.copy()
                alert["alert_type"] = self._get_alert_type(class_name, distance)
                alert["priority"] = self._get_priority_level(class_name, distance)
                alerts.append(alert)
        
        # Sort by priority (higher priority first)
        alerts.sort(key=lambda x: x["priority"], reverse=True)
        return alerts
    
    def _get_alert_type(self, class_name: str, distance: float) -> str:
        """Determine the type of alert for the detected object."""
        if distance < 0.8:
            return "immediate"
        elif distance < 1.5:
            return "warning"
        else:
            return "caution"
    
    def _get_priority_level(self, class_name: str, distance: float) -> int:
        """Calculate priority level for alerts (1-10, 10 is highest)."""
        base_priority = {
            "person": 8,
            "car": 9,
            "truck": 10,
            "bus": 10,
            "motorcycle": 9,
            "bicycle": 7,
            "stairs": 8,
            "pothole": 6,
            "stop sign": 5,
            "traffic light": 5
        }.get(class_name, 5)
        
        # Adjust priority based on distance
        if distance < 0.8:
            return min(10, base_priority + 2)
        elif distance < 1.5:
            return base_priority
        else:
            return max(1, base_priority - 1)
    
    def get_current_frame(self) -> Optional[np.ndarray]:
        """Get the current camera frame for display."""
        return self._get_frame()
    
    def get_annotated_frame(self) -> Optional[np.ndarray]:
        """Get the current frame with detection annotations."""
        frame = self._get_frame()
        if frame is None:
            return None
        
        detections = self.get_current_detections()
        
        # Draw detection boxes and labels
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            class_name = detection["class"]
            confidence = detection["confidence"]
            distance = detection["distance"]
            
            # Choose color based on distance
            if distance < 1.0:
                color = (0, 0, 255)  # Red for close objects
            elif distance < 2.0:
                color = (0, 165, 255)  # Orange for moderate distance
            else:
                color = (0, 255, 0)  # Green for far objects
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name}: {distance:.1f}m ({confidence:.2f})"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(frame, (x1, y1-label_size[1]-10), (x1+label_size[0], y1), color, -1)
            cv2.putText(frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame


# Example usage and testing
if __name__ == "__main__":
    import time
    
    detector = ObstacleDetector()
    
    try:
        # Start detection in mock mode
        detector.start_detection(use_mock=True)
        
        print("Running obstacle detection for 10 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            detections = detector.get_current_detections()
            alerts = detector.get_priority_alerts()
            
            if alerts:
                print(f"ALERTS: {len(alerts)} objects detected")
                for alert in alerts:
                    print(f"  - {alert['class']} at {alert['distance']:.1f}m ({alert['alert_type']})")
            
            time.sleep(1.0)
    
    finally:
        detector.stop_detection()
        print("Detection stopped")