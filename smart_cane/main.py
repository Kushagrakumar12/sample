"""
Smart Cane Main Application

Main entry point for the comprehensive smart cane system.
Integrates all modules and provides a unified interface.
"""

import os
import sys
import json
import threading
import time
import signal
from pathlib import Path
from typing import Optional

# Add the modules directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

# Import system modules
from modules.obstacle_detector import ObstacleDetector
from modules.navigation_system import NavigationSystem
from modules.voice_feedback import VoiceFeedbackSystem, AlertPriority, AlertType

# Try to import GUI module (may not be available in all environments)
try:
    from modules.gui_interface import SmartCaneGUI
    GUI_AVAILABLE = True
except ImportError as e:
    print(f"GUI not available: {e}. Running in CLI-only mode.")
    SmartCaneGUI = None
    GUI_AVAILABLE = False


class SmartCaneSystem:
    """
    Main Smart Cane system that integrates all modules and coordinates their operation.
    Provides a unified interface for obstacle detection, navigation, voice feedback, and GUI.
    """
    
    def __init__(self, config_dir: str = None):
        """Initialize the Smart Cane system."""
        # Set up configuration paths
        self.base_dir = Path(__file__).parent
        self.config_dir = Path(config_dir) if config_dir else self.base_dir / "config"
        
        # Load system configuration
        self.config = self._load_system_config()
        
        # Initialize system components
        self.obstacle_detector = None
        self.navigation_system = None
        self.voice_system = None
        self.gui = None
        
        # System state
        self.is_running = False
        self.start_time = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_system_config(self) -> dict:
        """Load the main system configuration."""
        config_file = self.config_dir / "settings.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config from {config_file}: {e}")
        
        # Return default configuration
        return {
            "system": {
                "auto_start": True,
                "use_gui": True,
                "simulation_mode": True,
                "debug_mode": False
            },
            "user_preferences": {
                "volume_level": 0.8,
                "speech_rate": 180,
                "alert_distance": 2.0,
                "voice_gender": "female",
                "language": "en"
            },
            "detection_settings": {
                "confidence_threshold": 0.5,
                "detection_classes": [
                    "person", "bicycle", "car", "motorcycle", "bus", "truck",
                    "traffic light", "stop sign", "bench", "fire hydrant"
                ]
            },
            "navigation_settings": {
                "walking_speed": 1.4,
                "route_update_interval": 5.0,
                "turn_announcement_distance": 10.0
            }
        }
    
    def initialize_components(self) -> bool:
        """Initialize all system components."""
        try:
            print("Initializing Smart Cane system components...")
            
            # Initialize Voice Feedback System
            print("- Initializing voice feedback system...")
            self.voice_system = VoiceFeedbackSystem(str(self.config_dir / "settings.json"))
            
            # Initialize Navigation System
            print("- Initializing navigation system...")
            self.navigation_system = NavigationSystem(str(self.config_dir / "settings.json"))
            
            # Initialize Obstacle Detection System
            print("- Initializing obstacle detection system...")
            self.obstacle_detector = ObstacleDetector(str(self.config_dir / "settings.json"))
            
            # Set up inter-module communication
            self._setup_callbacks()
            
            # Initialize GUI if enabled and available
            if self.config.get("system", {}).get("use_gui", True) and GUI_AVAILABLE:
                print("- Initializing graphical interface...")
                self.gui = SmartCaneGUI(str(self.config_dir / "settings.json"))
                self.gui.set_system_components(
                    obstacle_detector=self.obstacle_detector,
                    navigation_system=self.navigation_system,
                    voice_system=self.voice_system
                )
            elif self.config.get("system", {}).get("use_gui", True) and not GUI_AVAILABLE:
                print("- GUI requested but not available, using CLI mode")
                self.gui = None
            
            print("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            return False
    
    def _setup_callbacks(self):
        """Set up communication callbacks between modules."""
        # Navigation system callbacks
        if self.navigation_system and self.voice_system:
            self.navigation_system.set_callbacks(
                instruction_callback=self._on_navigation_instruction,
                arrival_callback=self._on_navigation_arrival,
                error_callback=self._on_navigation_error
            )
        
        # Set up obstacle detection alerts
        if self.obstacle_detector and self.voice_system:
            # Start a thread to monitor obstacle alerts
            alert_thread = threading.Thread(target=self._obstacle_alert_monitor)
            alert_thread.daemon = True
            alert_thread.start()
    
    def _on_navigation_instruction(self, instruction: str):
        """Handle navigation instruction callback."""
        if self.voice_system:
            self.voice_system.speak_navigation_instruction(instruction)
    
    def _on_navigation_arrival(self, message: str):
        """Handle navigation arrival callback."""
        if self.voice_system:
            self.voice_system.speak(message, AlertPriority.HIGH, AlertType.NAVIGATION)
    
    def _on_navigation_error(self, error_message: str):
        """Handle navigation error callback."""
        if self.voice_system:
            self.voice_system.speak(f"Navigation error: {error_message}", 
                                  AlertPriority.HIGH, AlertType.SYSTEM)
    
    def _obstacle_alert_monitor(self):
        """Monitor obstacle detection for alerts."""
        last_alert_time = {}
        alert_cooldown = 2.0  # Minimum seconds between same alerts
        
        while self.is_running:
            try:
                if self.obstacle_detector and self.voice_system:
                    alerts = self.obstacle_detector.get_priority_alerts()
                    
                    for alert in alerts:
                        obstacle_class = alert["class"]
                        distance = alert["distance"]
                        current_time = time.time()
                        
                        # Check cooldown to prevent spam
                        last_time = last_alert_time.get(obstacle_class, 0)
                        if current_time - last_time > alert_cooldown:
                            # Determine direction (simplified)
                            center_x = alert["center"][0]
                            if center_x < 213:  # Left third
                                direction = "to the left"
                            elif center_x > 426:  # Right third
                                direction = "to the right"
                            else:
                                direction = "ahead"
                            
                            # Send alert to voice system
                            self.voice_system.speak_obstacle_alert(
                                obstacle_class, distance, direction
                            )
                            
                            last_alert_time[obstacle_class] = current_time
                
                time.sleep(0.5)  # Check twice per second
                
            except Exception as e:
                print(f"Obstacle alert monitor error: {e}")
                time.sleep(1.0)
    
    def start(self) -> bool:
        """Start the Smart Cane system."""
        if self.is_running:
            print("System is already running")
            return True
        
        print("🚀 Starting Smart Cane System...")
        self.start_time = time.time()
        self.is_running = True
        
        try:
            # Start voice system
            if self.voice_system:
                self.voice_system.start()
                self.voice_system.speak("Smart Cane system starting up", 
                                      AlertPriority.MEDIUM, AlertType.SYSTEM)
            
            # Start obstacle detection
            if self.obstacle_detector:
                simulation_mode = self.config.get("system", {}).get("simulation_mode", True)
                self.obstacle_detector.start_detection(use_mock=simulation_mode)
            
            # Auto-start systems if configured
            if self.config.get("system", {}).get("auto_start", False):
                self._auto_start_systems()
            
            # Start GUI (this will block until GUI closes)
            if self.gui:
                print("🖥️  Starting graphical interface...")
                if self.voice_system:
                    self.voice_system.speak("System ready. GUI interface starting.", 
                                          AlertPriority.MEDIUM, AlertType.SYSTEM)
                self.gui.start()  # This blocks
            else:
                # Run in command-line mode
                self._run_cli_mode()
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start system: {e}")
            return False
    
    def _auto_start_systems(self):
        """Automatically start systems based on configuration."""
        if self.voice_system:
            self.voice_system.speak("Auto-starting all systems", 
                                  AlertPriority.LOW, AlertType.SYSTEM)
        
        # Add any auto-start logic here
        print("Auto-start systems activated")
    
    def _run_cli_mode(self):
        """Run the system in command-line mode without GUI."""
        print("\n" + "="*50)
        print("🦯 SMART CANE SYSTEM - CLI MODE")
        print("="*50)
        print("Available commands:")
        print("  nav <destination>  - Start navigation")
        print("  stop              - Stop navigation")
        print("  emergency         - Trigger emergency alert")
        print("  status            - Show system status")
        print("  help              - Show this help")
        print("  quit              - Exit system")
        print("="*50)
        
        try:
            while self.is_running:
                try:
                    command = input("\nsmart_cane> ").strip().lower()
                    
                    if command == "quit" or command == "exit":
                        break
                    elif command == "help":
                        self._show_cli_help()
                    elif command == "status":
                        self._show_system_status()
                    elif command == "emergency":
                        self._trigger_cli_emergency()
                    elif command.startswith("nav "):
                        destination = command[4:].strip()
                        self._start_cli_navigation(destination)
                    elif command == "stop":
                        self._stop_cli_navigation()
                    elif command:
                        print(f"Unknown command: {command}. Type 'help' for available commands.")
                        
                except KeyboardInterrupt:
                    print("\nPress Ctrl+C again to quit, or type 'quit'")
                except EOFError:
                    break
        
        except KeyboardInterrupt:
            print("\nShutting down...")
    
    def _show_cli_help(self):
        """Show CLI help information."""
        print("""
Smart Cane CLI Commands:

Navigation:
  nav <destination>     Start navigation to destination
  stop                  Stop current navigation
  
System:
  status               Show current system status
  emergency            Trigger emergency alert
  help                 Show this help message
  quit                 Exit the system

Examples:
  nav library          Navigate to library
  nav home             Navigate to home
  status               Check system status
""")
    
    def _show_system_status(self):
        """Show system status in CLI mode."""
        print("\n" + "="*40)
        print("SYSTEM STATUS")
        print("="*40)
        
        uptime = time.time() - self.start_time if self.start_time else 0
        print(f"Uptime: {uptime:.1f} seconds")
        
        if self.voice_system:
            voice_status = self.voice_system.get_system_status()
            print(f"Voice System: {'Running' if voice_status['is_running'] else 'Stopped'}")
            print(f"Queue Size: {voice_status['queue_size']}")
        
        if self.obstacle_detector:
            detections = self.obstacle_detector.get_current_detections()
            alerts = self.obstacle_detector.get_priority_alerts()
            print(f"Objects Detected: {len(detections)}")
            print(f"Active Alerts: {len(alerts)}")
        
        if self.navigation_system:
            nav_status = self.navigation_system.get_navigation_status()
            print(f"Navigation: {nav_status['state']}")
            if nav_status['state'] != 'idle':
                print(f"Progress: {nav_status['progress_percentage']:.1f}%")
        
        print("="*40)
    
    def _trigger_cli_emergency(self):
        """Trigger emergency alert in CLI mode."""
        print("🚨 EMERGENCY ALERT TRIGGERED!")
        if self.voice_system:
            self.voice_system.trigger_emergency_alert("CLI Mode Location")
    
    def _start_cli_navigation(self, destination: str):
        """Start navigation in CLI mode."""
        if not destination:
            print("Please specify a destination")
            return
        
        if self.navigation_system:
            print(f"Starting navigation to: {destination}")
            success = self.navigation_system.start_navigation(destination)
            if success:
                print("✅ Navigation started successfully")
            else:
                print("❌ Failed to start navigation")
        else:
            print("❌ Navigation system not available")
    
    def _stop_cli_navigation(self):
        """Stop navigation in CLI mode."""
        if self.navigation_system:
            self.navigation_system.stop_navigation()
            print("✅ Navigation stopped")
        else:
            print("❌ Navigation system not available")
    
    def stop(self):
        """Stop the Smart Cane system."""
        if not self.is_running:
            return
        
        print("🛑 Stopping Smart Cane System...")
        self.is_running = False
        
        # Stop all components
        try:
            if self.voice_system:
                self.voice_system.speak("System shutting down", 
                                      AlertPriority.HIGH, AlertType.SYSTEM)
                time.sleep(2)  # Give time for message to play
                self.voice_system.stop()
            
            if self.navigation_system:
                self.navigation_system.stop_navigation()
            
            if self.obstacle_detector:
                self.obstacle_detector.stop_detection()
            
            if self.gui:
                self.gui.stop()
            
            print("✅ Smart Cane system stopped successfully")
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        print(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.stop()
        sys.exit(0)
    
    def run_diagnostics(self) -> dict:
        """Run system diagnostics and return results."""
        print("Running system diagnostics...")
        
        results = {
            "timestamp": time.time(),
            "components": {},
            "overall_status": "unknown"
        }
        
        # Test voice system
        if self.voice_system:
            try:
                voice_status = self.voice_system.get_system_status()
                results["components"]["voice_system"] = {
                    "status": "ok" if voice_status["is_running"] else "stopped",
                    "details": voice_status
                }
            except Exception as e:
                results["components"]["voice_system"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Test obstacle detection
        if self.obstacle_detector:
            try:
                detections = self.obstacle_detector.get_current_detections()
                results["components"]["obstacle_detector"] = {
                    "status": "ok",
                    "detections_count": len(detections)
                }
            except Exception as e:
                results["components"]["obstacle_detector"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Test navigation system
        if self.navigation_system:
            try:
                nav_status = self.navigation_system.get_navigation_status()
                results["components"]["navigation_system"] = {
                    "status": "ok",
                    "nav_state": nav_status["state"]
                }
            except Exception as e:
                results["components"]["navigation_system"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Determine overall status
        component_statuses = [comp.get("status") for comp in results["components"].values()]
        if all(status == "ok" for status in component_statuses):
            results["overall_status"] = "healthy"
        elif any(status == "error" for status in component_statuses):
            results["overall_status"] = "error"
        else:
            results["overall_status"] = "warning"
        
        print(f"Diagnostics complete. Overall status: {results['overall_status']}")
        return results


def main():
    """Main entry point for the Smart Cane application."""
    print("🦯 Smart Cane System v1.0")
    print("Advanced Navigation and Safety System for Visually Impaired Users")
    print("=" * 60)
    
    # Create system instance
    smart_cane = SmartCaneSystem()
    
    try:
        # Initialize all components
        if not smart_cane.initialize_components():
            print("❌ Failed to initialize system components")
            return 1
        
        # Run diagnostics
        diagnostics = smart_cane.run_diagnostics()
        if diagnostics["overall_status"] != "healthy":
            print(f"⚠️  System diagnostics show status: {diagnostics['overall_status']}")
            print("Some components may not function properly.")
        
        # Start the system
        if not smart_cane.start():
            print("❌ Failed to start system")
            return 1
    
    except KeyboardInterrupt:
        print("\n🛑 System interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    finally:
        # Always attempt graceful shutdown
        try:
            smart_cane.stop()
        except Exception as e:
            print(f"Error during shutdown: {e}")
    
    print("👋 Smart Cane system shutdown complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())