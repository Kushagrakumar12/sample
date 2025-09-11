"""
Tests for the Obstacle Detection module.
"""

import unittest
import time
import numpy as np
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from obstacle_detector import ObstacleDetector


class TestObstacleDetector(unittest.TestCase):
    """Test cases for ObstacleDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = ObstacleDetector()
    
    def tearDown(self):
        """Clean up after tests."""
        if self.detector.is_running:
            self.detector.stop_detection()
    
    def test_initialization(self):
        """Test detector initialization."""
        self.assertIsNotNone(self.detector)
        self.assertFalse(self.detector.is_running)
        self.assertEqual(len(self.detector.current_detections), 0)
    
    def test_start_stop_detection(self):
        """Test starting and stopping detection."""
        # Start detection
        self.detector.start_detection(use_mock=True)
        self.assertTrue(self.detector.is_running)
        
        # Stop detection
        self.detector.stop_detection()
        self.assertFalse(self.detector.is_running)
    
    def test_mock_detection(self):
        """Test mock detection functionality."""
        # Generate mock frame
        frame = self.detector._generate_mock_frame()
        self.assertIsInstance(frame, np.ndarray)
        self.assertEqual(frame.shape, (480, 640, 3))
        
        # Test mock detection
        detections = self.detector._mock_detection(frame)
        self.assertIsInstance(detections, list)
        self.assertGreater(len(detections), 0)
        
        # Verify detection structure
        for detection in detections:
            self.assertIn('class', detection)
            self.assertIn('confidence', detection)
            self.assertIn('bbox', detection)
            self.assertIn('distance', detection)
            self.assertIn('center', detection)
    
    def test_distance_estimation(self):
        """Test distance estimation algorithm."""
        # Test person detection
        distance = self.detector._estimate_distance(100, 100, 200, 300, "person")
        self.assertGreater(distance, 0)
        self.assertLess(distance, 20.0)
        
        # Test car detection
        distance = self.detector._estimate_distance(100, 100, 300, 200, "car")
        self.assertGreater(distance, 0)
        self.assertLess(distance, 20.0)
    
    def test_priority_alerts(self):
        """Test priority alert system."""
        # Start detection to get some mock data
        self.detector.start_detection(use_mock=True)
        time.sleep(0.5)  # Allow some detections
        
        # Get priority alerts
        alerts = self.detector.get_priority_alerts()
        self.assertIsInstance(alerts, list)
        
        # Test alert structure
        for alert in alerts:
            self.assertIn('alert_type', alert)
            self.assertIn('priority', alert)
            self.assertIn('class', alert)
            self.assertIn('distance', alert)
    
    def test_get_current_detections(self):
        """Test getting current detections."""
        detections = self.detector.get_current_detections()
        self.assertIsInstance(detections, list)
    
    def test_class_names_loading(self):
        """Test class names loading."""
        self.assertIsInstance(self.detector.class_names, list)
        self.assertGreater(len(self.detector.class_names), 0)
        self.assertIn("person", self.detector.class_names)
    
    def test_alert_priorities(self):
        """Test alert priority calculation."""
        # Test high priority (close person)
        priority = self.detector._get_priority_level("person", 0.5)
        self.assertGreaterEqual(priority, 8)
        
        # Test medium priority (far car)
        priority = self.detector._get_priority_level("car", 3.0)
        self.assertLessEqual(priority, 9)
        
        # Test low priority (far object)
        priority = self.detector._get_priority_level("bench", 5.0)
        self.assertLessEqual(priority, 6)
    
    def test_alert_types(self):
        """Test alert type determination."""
        # Immediate alert
        alert_type = self.detector._get_alert_type("person", 0.5)
        self.assertEqual(alert_type, "immediate")
        
        # Warning alert
        alert_type = self.detector._get_alert_type("car", 1.2)
        self.assertEqual(alert_type, "warning")
        
        # Caution alert
        alert_type = self.detector._get_alert_type("bench", 2.0)
        self.assertEqual(alert_type, "caution")
    
    def test_annotated_frame(self):
        """Test annotated frame generation."""
        self.detector.start_detection(use_mock=True)
        time.sleep(0.2)  # Allow some processing
        
        frame = self.detector.get_annotated_frame()
        if frame is not None:
            self.assertIsInstance(frame, np.ndarray)
            self.assertEqual(len(frame.shape), 3)  # Should be color image


class TestObstacleDetectorIntegration(unittest.TestCase):
    """Integration tests for ObstacleDetector."""
    
    def test_continuous_detection(self):
        """Test continuous detection over time."""
        detector = ObstacleDetector()
        
        try:
            detector.start_detection(use_mock=True)
            
            # Run for a few seconds and collect detections
            detections_over_time = []
            for _ in range(5):
                time.sleep(0.5)
                detections = detector.get_current_detections()
                detections_over_time.append(len(detections))
            
            # Should have some detections
            self.assertTrue(any(count > 0 for count in detections_over_time))
            
        finally:
            detector.stop_detection()
    
    def test_alert_generation_over_time(self):
        """Test alert generation over time."""
        detector = ObstacleDetector()
        
        try:
            detector.start_detection(use_mock=True)
            
            # Collect alerts over time
            alerts_over_time = []
            for _ in range(5):
                time.sleep(0.5)
                alerts = detector.get_priority_alerts()
                alerts_over_time.append(len(alerts))
            
            # Should generate some alerts (mock objects are close)
            self.assertTrue(any(count > 0 for count in alerts_over_time))
            
        finally:
            detector.stop_detection()


if __name__ == '__main__':
    unittest.main()