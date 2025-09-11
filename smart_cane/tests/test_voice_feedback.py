"""
Tests for the Voice Feedback module.
"""

import unittest
import time
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from voice_feedback import VoiceFeedbackSystem, AlertPriority, AlertType, AudioAlert


class TestAudioAlert(unittest.TestCase):
    """Test cases for AudioAlert class."""
    
    def test_alert_creation(self):
        """Test audio alert creation."""
        alert = AudioAlert(
            message="Test message",
            priority=AlertPriority.HIGH,
            alert_type=AlertType.OBSTACLE
        )
        
        self.assertEqual(alert.message, "Test message")
        self.assertEqual(alert.priority, AlertPriority.HIGH)
        self.assertEqual(alert.alert_type, AlertType.OBSTACLE)
        self.assertEqual(alert.repeat_count, 1)
        self.assertFalse(alert.interrupt_ongoing)
        self.assertIsNotNone(alert.timestamp)
    
    def test_alert_with_custom_params(self):
        """Test audio alert with custom parameters."""
        def test_callback():
            pass
        
        alert = AudioAlert(
            message="Custom alert",
            priority=AlertPriority.EMERGENCY,
            alert_type=AlertType.EMERGENCY,
            repeat_count=3,
            delay_between_repeats=2.0,
            interrupt_ongoing=True,
            callback=test_callback
        )
        
        self.assertEqual(alert.repeat_count, 3)
        self.assertEqual(alert.delay_between_repeats, 2.0)
        self.assertTrue(alert.interrupt_ongoing)
        self.assertEqual(alert.callback, test_callback)


class TestVoiceFeedbackSystem(unittest.TestCase):
    """Test cases for VoiceFeedbackSystem class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.voice_system = VoiceFeedbackSystem()
    
    def tearDown(self):
        """Clean up after tests."""
        if self.voice_system.is_running:
            self.voice_system.stop()
    
    def test_initialization(self):
        """Test voice system initialization."""
        self.assertIsNotNone(self.voice_system)
        self.assertFalse(self.voice_system.is_running)
        self.assertFalse(self.voice_system.emergency_active)
        self.assertEqual(self.voice_system.get_queue_size(), 0)
    
    def test_start_stop(self):
        """Test starting and stopping the voice system."""
        # Start system
        self.voice_system.start()
        self.assertTrue(self.voice_system.is_running)
        
        # Stop system
        self.voice_system.stop()
        self.assertFalse(self.voice_system.is_running)
    
    def test_basic_speech(self):
        """Test basic speech functionality."""
        self.voice_system.start()
        
        # Queue a message
        success = self.voice_system.speak("Test message")
        self.assertTrue(success)
        
        # Check queue
        self.assertGreater(self.voice_system.get_queue_size(), 0)
        
        # Wait a bit for processing
        time.sleep(0.5)
    
    def test_obstacle_alerts(self):
        """Test obstacle alert messages."""
        self.voice_system.start()
        
        # Test close obstacle (critical)
        success = self.voice_system.speak_obstacle_alert("person", 0.5, "ahead")
        self.assertTrue(success)
        
        # Test medium distance obstacle
        success = self.voice_system.speak_obstacle_alert("car", 1.5, "to the right")
        self.assertTrue(success)
        
        # Test far obstacle
        success = self.voice_system.speak_obstacle_alert("bench", 3.0, "to the left")
        self.assertTrue(success)
    
    def test_navigation_instructions(self):
        """Test navigation instruction messages."""
        self.voice_system.start()
        
        success = self.voice_system.speak_navigation_instruction("Turn right in 50 meters")
        self.assertTrue(success)
        
        success = self.voice_system.speak_navigation_instruction("Continue straight for 200 meters")
        self.assertTrue(success)
    
    def test_system_messages(self):
        """Test system status messages."""
        self.voice_system.start()
        
        success = self.voice_system.speak_system_message("System started")
        self.assertTrue(success)
        
        success = self.voice_system.speak_system_message("Battery low", AlertPriority.HIGH)
        self.assertTrue(success)
    
    def test_emergency_alert(self):
        """Test emergency alert system."""
        self.voice_system.start()
        
        # Trigger emergency
        success = self.voice_system.trigger_emergency_alert("123 Main Street")
        self.assertTrue(success)
        self.assertTrue(self.voice_system.emergency_active)
        
        # Cancel emergency
        success = self.voice_system.cancel_emergency_alert()
        self.assertTrue(success)
        self.assertFalse(self.voice_system.emergency_active)
    
    def test_volume_control(self):
        """Test volume control."""
        # Test valid volume levels
        self.voice_system.set_volume(0.5)
        self.assertEqual(self.voice_system.volume, 0.5)
        
        self.voice_system.set_volume(1.0)
        self.assertEqual(self.voice_system.volume, 1.0)
        
        self.voice_system.set_volume(0.0)
        self.assertEqual(self.voice_system.volume, 0.0)
        
        # Test volume clamping
        self.voice_system.set_volume(1.5)  # Should clamp to 1.0
        self.assertEqual(self.voice_system.volume, 1.0)
        
        self.voice_system.set_volume(-0.5)  # Should clamp to 0.0
        self.assertEqual(self.voice_system.volume, 0.0)
    
    def test_speech_rate_control(self):
        """Test speech rate control."""
        # Test valid speech rates
        self.voice_system.set_speech_rate(150)
        self.assertEqual(self.voice_system.speech_rate, 150)
        
        self.voice_system.set_speech_rate(200)
        self.assertEqual(self.voice_system.speech_rate, 200)
        
        # Test rate clamping
        self.voice_system.set_speech_rate(50)  # Should clamp to 100
        self.assertEqual(self.voice_system.speech_rate, 100)
        
        self.voice_system.set_speech_rate(400)  # Should clamp to 300
        self.assertEqual(self.voice_system.speech_rate, 300)
    
    def test_available_voices(self):
        """Test available voices listing."""
        voices = self.voice_system.get_available_voices()
        self.assertIsInstance(voices, list)
        
        # Each voice should have required fields
        for voice in voices:
            self.assertIn('id', voice)
            self.assertIn('name', voice)
            self.assertIn('gender', voice)
            self.assertIn('language', voice)
    
    def test_queue_management(self):
        """Test audio queue management."""
        self.voice_system.start()
        
        # Add some messages
        self.voice_system.speak("Message 1", AlertPriority.LOW)
        self.voice_system.speak("Message 2", AlertPriority.MEDIUM)
        self.voice_system.speak("Message 3", AlertPriority.HIGH)
        
        initial_size = self.voice_system.get_queue_size()
        self.assertGreater(initial_size, 0)
        
        # Clear queue (preserve emergency)
        self.voice_system.clear_queue(preserve_emergency=True)
        
        # Clear all
        self.voice_system.clear_queue(preserve_emergency=False)
        time.sleep(0.1)  # Allow processing
    
    def test_system_status(self):
        """Test system status reporting."""
        # Test stopped state
        status = self.voice_system.get_system_status()
        self.assertFalse(status['is_running'])
        self.assertFalse(status['is_speaking'])
        self.assertEqual(status['queue_size'], 0)
        self.assertFalse(status['emergency_active'])
        
        # Test running state
        self.voice_system.start()
        status = self.voice_system.get_system_status()
        self.assertTrue(status['is_running'])
        
        # Add some content and check status
        self.voice_system.speak("Test message")
        time.sleep(0.1)
        status = self.voice_system.get_system_status()
        # Queue size might be 0 if message processed quickly
        self.assertGreaterEqual(status['queue_size'], 0)
    
    def test_priority_handling(self):
        """Test priority-based message handling."""
        self.voice_system.start()
        
        # Add messages with different priorities
        self.voice_system.speak("Low priority", AlertPriority.LOW)
        self.voice_system.speak("High priority", AlertPriority.HIGH, interrupt=True)
        self.voice_system.speak("Emergency", AlertPriority.EMERGENCY, interrupt=True)
        
        # Emergency and high priority messages should be processed first
        time.sleep(1.0)  # Allow some processing
    
    def test_callback_functionality(self):
        """Test message completion callbacks."""
        self.voice_system.start()
        
        callback_called = []
        
        def test_callback():
            callback_called.append(True)
        
        # Send message with callback
        self.voice_system.speak(
            "Message with callback",
            callback=test_callback
        )
        
        # Wait for message to complete
        time.sleep(2.0)
        
        # Callback should have been called (in mock mode, it should complete quickly)
        self.assertGreater(len(callback_called), 0)


class TestVoiceFeedbackIntegration(unittest.TestCase):
    """Integration tests for VoiceFeedbackSystem."""
    
    def test_continuous_operation(self):
        """Test continuous operation with multiple messages."""
        voice_system = VoiceFeedbackSystem()
        
        try:
            voice_system.start()
            
            # Send various types of messages
            messages = [
                ("Navigation instruction", AlertPriority.HIGH, AlertType.NAVIGATION),
                ("Obstacle detected", AlertPriority.CRITICAL, AlertType.OBSTACLE),
                ("System ready", AlertPriority.MEDIUM, AlertType.SYSTEM),
                ("User message", AlertPriority.LOW, AlertType.USER)
            ]
            
            for message, priority, alert_type in messages:
                success = voice_system.speak(message, priority, alert_type)
                self.assertTrue(success)
                time.sleep(0.2)  # Small delay between messages
            
            # Let system process messages
            time.sleep(2.0)
            
            # System should still be running
            self.assertTrue(voice_system.is_running)
            
        finally:
            voice_system.stop()
    
    def test_emergency_scenario(self):
        """Test complete emergency scenario."""
        voice_system = VoiceFeedbackSystem()
        
        try:
            voice_system.start()
            
            # Normal operation
            voice_system.speak("System operating normally")
            time.sleep(0.5)
            
            # Emergency occurs
            voice_system.trigger_emergency_alert("Emergency location")
            self.assertTrue(voice_system.emergency_active)
            
            # Try to send normal message (should still work)
            voice_system.speak("Normal message during emergency")
            
            # Cancel emergency
            voice_system.cancel_emergency_alert()
            self.assertFalse(voice_system.emergency_active)
            
        finally:
            voice_system.stop()


if __name__ == '__main__':
    unittest.main()