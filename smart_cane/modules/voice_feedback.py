"""
Module 3: User Feedback & Alerts

This module provides comprehensive audio feedback using text-to-speech,
emergency alert system, and customizable voice settings.
"""

import threading
import time
import json
import os
import queue
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import tempfile

try:
    import pyttsx3
except ImportError:
    print("Warning: pyttsx3 not available. Using mock TTS.")
    pyttsx3 = None

try:
    from gtts import gTTS
    import pygame
except ImportError:
    print("Warning: gTTS or pygame not available. Using fallback TTS.")
    gTTS = None
    pygame = None


class AlertPriority(Enum):
    """Priority levels for audio alerts."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class AlertType(Enum):
    """Types of audio alerts."""
    NAVIGATION = "navigation"
    OBSTACLE = "obstacle"
    SYSTEM = "system"
    EMERGENCY = "emergency"
    USER = "user"


@dataclass
class AudioAlert:
    """Represents an audio alert message."""
    message: str
    priority: AlertPriority
    alert_type: AlertType
    repeat_count: int = 1
    delay_between_repeats: float = 1.0
    interrupt_ongoing: bool = False
    callback: Optional[Callable] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class VoiceFeedbackSystem:
    """
    Comprehensive voice feedback and alert system for the smart cane.
    Manages text-to-speech, audio alerts, and emergency notifications.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the voice feedback system."""
        self.config = self._load_config(config_path)
        
        # TTS engines
        self.pyttsx3_engine = None
        self.gtts_enabled = False
        self.mock_mode = False
        
        # Audio system
        self.audio_queue = queue.PriorityQueue()
        self.is_speaking = False
        self.current_alert = None
        
        # Threading
        self.audio_thread = None
        self.is_running = False
        self.audio_lock = threading.Lock()
        
        # Emergency system
        self.emergency_active = False
        self.emergency_contacts = []
        
        # Voice settings
        self.volume = 0.8
        self.speech_rate = 180
        self.voice_id = None
        
        self._initialize_tts()
        self._load_emergency_contacts()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load voice feedback configuration."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "user_preferences": {
                "volume_level": 0.8,
                "speech_rate": 180,
                "voice_gender": "female",
                "language": "en"
            },
            "emergency_settings": {
                "emergency_contacts": [
                    {"name": "Emergency Services", "number": "911"},
                    {"name": "Family Contact", "number": "+1234567890"}
                ],
                "auto_alert_timeout": 30.0
            }
        }
    
    def _initialize_tts(self):
        """Initialize text-to-speech engines."""
        # Try to initialize pyttsx3
        if pyttsx3:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                self._configure_pyttsx3()
                print("pyttsx3 TTS engine initialized")
            except Exception as e:
                print(f"Failed to initialize pyttsx3: {e}")
                self.pyttsx3_engine = None
        
        # Try to initialize gTTS and pygame
        if gTTS and pygame:
            try:
                pygame.mixer.init()
                self.gtts_enabled = True
                print("gTTS with pygame initialized")
            except Exception as e:
                print(f"Failed to initialize gTTS/pygame: {e}")
                self.gtts_enabled = False
        
        # If no TTS engines available, use mock mode
        if not self.pyttsx3_engine and not self.gtts_enabled:
            print("No TTS engines available. Using mock mode.")
            self.mock_mode = True
    
    def _configure_pyttsx3(self):
        """Configure pyttsx3 settings."""
        if not self.pyttsx3_engine:
            return
        
        try:
            # Set speech rate
            rate = self.config["user_preferences"]["speech_rate"]
            self.pyttsx3_engine.setProperty('rate', rate)
            
            # Set volume
            volume = self.config["user_preferences"]["volume_level"]
            self.pyttsx3_engine.setProperty('volume', volume)
            
            # Set voice (prefer female if available)
            voices = self.pyttsx3_engine.getProperty('voices')
            preferred_gender = self.config["user_preferences"]["voice_gender"]
            
            selected_voice = None
            for voice in voices:
                if preferred_gender.lower() in voice.name.lower():
                    selected_voice = voice
                    break
            
            if not selected_voice and voices:
                selected_voice = voices[0]  # Use first available
            
            if selected_voice:
                self.pyttsx3_engine.setProperty('voice', selected_voice.id)
                self.voice_id = selected_voice.id
                
        except Exception as e:
            print(f"Error configuring pyttsx3: {e}")
    
    def _load_emergency_contacts(self):
        """Load emergency contact information."""
        try:
            contacts = self.config["emergency_settings"]["emergency_contacts"]
            self.emergency_contacts = contacts
        except KeyError:
            self.emergency_contacts = [
                {"name": "Emergency Services", "number": "911"}
            ]
    
    def start(self):
        """Start the voice feedback system."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start audio processing thread
        self.audio_thread = threading.Thread(target=self._audio_processing_loop)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        print("Voice feedback system started")
    
    def stop(self):
        """Stop the voice feedback system."""
        self.is_running = False
        
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        # Wait for thread to finish
        if self.audio_thread:
            self.audio_thread.join(timeout=2.0)
        
        # Clean up TTS engine
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.stop()
            except:
                pass
        
        # Clean up pygame
        if pygame and pygame.mixer.get_init():
            pygame.mixer.quit()
        
        print("Voice feedback system stopped")
    
    def speak(self, message: str, priority: AlertPriority = AlertPriority.MEDIUM,
              alert_type: AlertType = AlertType.SYSTEM, 
              interrupt: bool = False, callback: Callable = None) -> bool:
        """
        Speak a message with specified priority and type.
        
        Args:
            message: Text to speak
            priority: Priority level of the message
            alert_type: Type of alert
            interrupt: Whether to interrupt ongoing speech
            callback: Function to call when speech completes
        
        Returns:
            True if message was queued successfully
        """
        if not self.is_running:
            return False
        
        alert = AudioAlert(
            message=message,
            priority=priority,
            alert_type=alert_type,
            interrupt_ongoing=interrupt,
            callback=callback
        )
        
        try:
            # Use negative priority for queue (higher priority = lower number)
            queue_priority = -priority.value
            self.audio_queue.put((queue_priority, alert.timestamp, alert))
            
            # If this is high priority and should interrupt, stop current speech
            if interrupt and priority.value >= AlertPriority.HIGH.value:
                self._interrupt_current_speech()
            
            return True
        except Exception as e:
            print(f"Error queuing speech: {e}")
            return False
    
    def speak_obstacle_alert(self, obstacle_class: str, distance: float, 
                           direction: str = "ahead") -> bool:
        """Speak an obstacle detection alert."""
        if distance < 0.8:
            urgency = "immediately"
            priority = AlertPriority.CRITICAL
        elif distance < 1.5:
            urgency = "soon"
            priority = AlertPriority.HIGH
        else:
            urgency = ""
            priority = AlertPriority.MEDIUM
        
        # Format obstacle message
        distance_str = f"{distance:.1f} meters" if distance >= 1.0 else f"{int(distance * 100)} centimeters"
        
        if urgency:
            message = f"Caution! {obstacle_class} {urgency} {direction}, {distance_str} away"
        else:
            message = f"{obstacle_class} detected {direction}, {distance_str} away"
        
        return self.speak(message, priority, AlertType.OBSTACLE, interrupt=(priority.value >= 4))
    
    def speak_navigation_instruction(self, instruction: str) -> bool:
        """Speak a navigation instruction."""
        return self.speak(instruction, AlertPriority.HIGH, AlertType.NAVIGATION, interrupt=True)
    
    def speak_system_message(self, message: str, priority: AlertPriority = AlertPriority.MEDIUM) -> bool:
        """Speak a system status message."""
        return self.speak(message, priority, AlertType.SYSTEM)
    
    def trigger_emergency_alert(self, location: str = None, auto_call: bool = False) -> bool:
        """Trigger an emergency alert with location sharing."""
        self.emergency_active = True
        
        # Construct emergency message
        emergency_message = "Emergency alert activated!"
        if location:
            emergency_message += f" Current location: {location}"
        
        emergency_message += " Notifying emergency contacts."
        
        # Speak emergency message with highest priority
        success = self.speak(
            emergency_message,
            AlertPriority.EMERGENCY,
            AlertType.EMERGENCY,
            interrupt=True
        )
        
        # Simulate emergency contact notification
        self._notify_emergency_contacts(location, auto_call)
        
        return success
    
    def _notify_emergency_contacts(self, location: str = None, auto_call: bool = False):
        """Simulate notifying emergency contacts."""
        print("\n🚨 EMERGENCY ALERT TRIGGERED 🚨")
        print("=" * 50)
        
        if location:
            print(f"📍 Location: {location}")
        else:
            print("📍 Location: GPS coordinates not available")
        
        print("📞 Notifying emergency contacts:")
        
        for contact in self.emergency_contacts:
            print(f"   - {contact['name']}: {contact['number']}")
            if auto_call:
                print(f"     → Auto-calling {contact['name']}... (SIMULATED)")
            else:
                print(f"     → SMS alert sent to {contact['name']} (SIMULATED)")
        
        print("=" * 50)
        
        # Speak confirmation
        self.speak(
            "Emergency contacts have been notified. Help is on the way.",
            AlertPriority.EMERGENCY,
            AlertType.EMERGENCY
        )
    
    def cancel_emergency_alert(self) -> bool:
        """Cancel the active emergency alert."""
        if not self.emergency_active:
            return False
        
        self.emergency_active = False
        message = "Emergency alert cancelled"
        print(f"✅ {message}")
        
        return self.speak(message, AlertPriority.HIGH, AlertType.EMERGENCY, interrupt=True)
    
    def set_volume(self, volume: float):
        """Set the speech volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.setProperty('volume', self.volume)
            except:
                pass
        
        # Update config
        self.config["user_preferences"]["volume_level"] = self.volume
    
    def set_speech_rate(self, rate: int):
        """Set the speech rate (words per minute)."""
        self.speech_rate = max(100, min(300, rate))  # Reasonable bounds
        
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.setProperty('rate', self.speech_rate)
            except:
                pass
        
        # Update config
        self.config["user_preferences"]["speech_rate"] = self.speech_rate
    
    def get_available_voices(self) -> List[Dict]:
        """Get list of available voices."""
        voices = []
        
        if self.pyttsx3_engine:
            try:
                engine_voices = self.pyttsx3_engine.getProperty('voices')
                for voice in engine_voices:
                    voices.append({
                        "id": voice.id,
                        "name": voice.name,
                        "gender": "female" if "female" in voice.name.lower() else "male",
                        "language": getattr(voice, 'languages', ['en'])[0] if hasattr(voice, 'languages') else 'en'
                    })
            except:
                pass
        
        return voices
    
    def set_voice(self, voice_id: str) -> bool:
        """Set the active voice."""
        if self.pyttsx3_engine:
            try:
                self.pyttsx3_engine.setProperty('voice', voice_id)
                self.voice_id = voice_id
                return True
            except:
                pass
        
        return False
    
    def _audio_processing_loop(self):
        """Main audio processing loop running in separate thread."""
        while self.is_running:
            try:
                # Get next audio alert from queue (blocking with timeout)
                try:
                    priority, timestamp, alert = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the alert
                self._process_audio_alert(alert)
                
                # Mark task as done
                self.audio_queue.task_done()
                
            except Exception as e:
                print(f"Audio processing error: {e}")
                time.sleep(0.1)
    
    def _process_audio_alert(self, alert: AudioAlert):
        """Process a single audio alert."""
        with self.audio_lock:
            self.is_speaking = True
            self.current_alert = alert
        
        try:
            # Repeat the message as specified
            for repeat in range(alert.repeat_count):
                if not self.is_running:
                    break
                
                if repeat > 0:
                    time.sleep(alert.delay_between_repeats)
                
                self._speak_text(alert.message)
            
            # Call completion callback if provided
            if alert.callback:
                try:
                    alert.callback()
                except Exception as e:
                    print(f"Alert callback error: {e}")
                    
        finally:
            with self.audio_lock:
                self.is_speaking = False
                self.current_alert = None
    
    def _speak_text(self, text: str):
        """Speak the given text using available TTS engine."""
        if self.mock_mode:
            self._mock_speak(text)
        elif self.pyttsx3_engine:
            self._speak_pyttsx3(text)
        elif self.gtts_enabled:
            self._speak_gtts(text)
        else:
            print(f"TTS: {text}")  # Fallback to console output
    
    def _speak_pyttsx3(self, text: str):
        """Speak text using pyttsx3 engine."""
        try:
            self.pyttsx3_engine.say(text)
            self.pyttsx3_engine.runAndWait()
        except Exception as e:
            print(f"pyttsx3 speech error: {e}")
            self._mock_speak(text)
    
    def _speak_gtts(self, text: str):
        """Speak text using gTTS and pygame."""
        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_filename)
            
            # Play audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                if not self.is_running:
                    pygame.mixer.music.stop()
                    break
            
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
                
        except Exception as e:
            print(f"gTTS speech error: {e}")
            self._mock_speak(text)
    
    def _mock_speak(self, text: str):
        """Mock speech for simulation (console output with timing)."""
        print(f"🗣️  TTS: {text}")
        
        # Simulate speech timing (roughly 150 words per minute)
        word_count = len(text.split())
        speech_duration = (word_count / 150) * 60  # Convert to seconds
        speech_duration = max(1.0, speech_duration)  # Minimum 1 second
        
        # Sleep to simulate speech duration
        time.sleep(speech_duration)
    
    def _interrupt_current_speech(self):
        """Interrupt currently ongoing speech."""
        try:
            if self.pyttsx3_engine:
                self.pyttsx3_engine.stop()
            
            if pygame and pygame.mixer.get_init():
                pygame.mixer.music.stop()
                
        except Exception as e:
            print(f"Error interrupting speech: {e}")
    
    def is_currently_speaking(self) -> bool:
        """Check if the system is currently speaking."""
        with self.audio_lock:
            return self.is_speaking
    
    def get_queue_size(self) -> int:
        """Get the current size of the audio queue."""
        return self.audio_queue.qsize()
    
    def clear_queue(self, preserve_emergency: bool = True):
        """Clear the audio queue."""
        if preserve_emergency:
            # Save emergency alerts
            emergency_alerts = []
            temp_queue = queue.PriorityQueue()
            
            while not self.audio_queue.empty():
                try:
                    item = self.audio_queue.get_nowait()
                    if item[2].alert_type == AlertType.EMERGENCY:
                        emergency_alerts.append(item)
                except queue.Empty:
                    break
            
            # Re-add emergency alerts
            for alert in emergency_alerts:
                self.audio_queue.put(alert)
        else:
            # Clear everything
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
    
    def get_system_status(self) -> Dict:
        """Get current status of the voice feedback system."""
        return {
            "is_running": self.is_running,
            "is_speaking": self.is_currently_speaking(),
            "queue_size": self.get_queue_size(),
            "emergency_active": self.emergency_active,
            "volume": self.volume,
            "speech_rate": self.speech_rate,
            "tts_engine": "pyttsx3" if self.pyttsx3_engine else ("gtts" if self.gtts_enabled else "mock"),
            "available_voices": len(self.get_available_voices())
        }


# Example usage and testing
if __name__ == "__main__":
    import time
    
    def completion_callback():
        print("✅ Speech completed")
    
    # Create voice feedback system
    voice_system = VoiceFeedbackSystem()
    
    try:
        # Start the system
        voice_system.start()
        
        print("Testing voice feedback system...")
        
        # Test basic speech
        voice_system.speak("Welcome to the Smart Cane system", AlertPriority.MEDIUM)
        time.sleep(2)
        
        # Test obstacle alerts
        voice_system.speak_obstacle_alert("person", 1.2, "ahead")
        time.sleep(3)
        
        voice_system.speak_obstacle_alert("car", 0.5, "to the right")
        time.sleep(3)
        
        # Test navigation instruction
        voice_system.speak_navigation_instruction("Turn right in 50 meters")
        time.sleep(3)
        
        # Test emergency alert
        print("\nTesting emergency alert...")
        voice_system.trigger_emergency_alert("123 Main Street, San Francisco")
        time.sleep(5)
        
        # Test system status
        status = voice_system.get_system_status()
        print(f"\nSystem status: {status}")
        
    finally:
        voice_system.stop()
        print("Voice feedback system test completed")