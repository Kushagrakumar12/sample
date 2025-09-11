"""
Module 2: Navigation System

This module provides GPS-based navigation with turn-by-turn voice guidance.
Integrates with Google Maps API for routing and includes indoor navigation simulation.
"""

import json
import math
import time
import threading
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import os

try:
    import googlemaps
except ImportError:
    print("Warning: googlemaps not available. Using mock navigation.")
    googlemaps = None


class NavigationState(Enum):
    """Navigation system states."""
    IDLE = "idle"
    PLANNING = "planning"
    NAVIGATING = "navigating"
    PAUSED = "paused"
    ARRIVED = "arrived"
    ERROR = "error"


@dataclass
class Location:
    """Represents a geographic location."""
    latitude: float
    longitude: float
    address: str = ""
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance to another location in meters."""
        return self._haversine_distance(
            self.latitude, self.longitude,
            other.latitude, other.longitude
        )
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on Earth."""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


@dataclass
class RouteStep:
    """Represents a single step in a navigation route."""
    instruction: str
    distance: float
    duration: float
    start_location: Location
    end_location: Location
    maneuver: str = ""
    
    def get_direction(self) -> str:
        """Get simplified direction from maneuver."""
        if "left" in self.maneuver.lower():
            return "left"
        elif "right" in self.maneuver.lower():
            return "right"
        elif "straight" in self.maneuver.lower() or "continue" in self.maneuver.lower():
            return "straight"
        else:
            return "forward"


class NavigationSystem:
    """
    GPS-based navigation system with voice guidance and route management.
    Supports both outdoor (Google Maps) and indoor (simulated) navigation.
    """
    
    def __init__(self, config_path: str = None, api_key: str = None):
        """Initialize the navigation system."""
        self.config = self._load_config(config_path)
        self.api_key = api_key or self._load_api_key()
        self.gmaps_client = None
        
        # Navigation state
        self.state = NavigationState.IDLE
        self.current_route = None
        self.current_step_index = 0
        self.current_location = None
        self.destination = None
        
        # Navigation thread
        self.navigation_thread = None
        self.is_navigating = False
        self.navigation_lock = threading.Lock()
        
        # Callbacks for events
        self.instruction_callback = None
        self.arrival_callback = None
        self.error_callback = None
        
        # Mock mode for simulation
        self.mock_mode = True
        self.mock_current_location = Location(37.7749, -122.4194, "San Francisco, CA")
        
        self._setup_gmaps_client()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load navigation configuration."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "navigation_settings": {
                "walking_speed": 1.4,  # m/s
                "route_update_interval": 5.0,
                "turn_announcement_distance": 10.0,
                "indoor_mode": False
            }
        }
    
    def _load_api_key(self) -> Optional[str]:
        """Load Google Maps API key from configuration."""
        try:
            config_dir = os.path.dirname(os.path.dirname(__file__))
            api_config_path = os.path.join(config_dir, "config", "api_keys.json")
            
            with open(api_config_path, 'r') as f:
                api_config = json.load(f)
                
            if api_config.get("simulation_mode", {}).get("use_mock_apis", True):
                return None  # Use mock mode
            
            return api_config.get("google_maps", {}).get("api_key")
        except (FileNotFoundError, KeyError):
            return None
    
    def _setup_gmaps_client(self):
        """Initialize Google Maps client."""
        if self.api_key and googlemaps:
            try:
                self.gmaps_client = googlemaps.Client(key=self.api_key)
                self.mock_mode = False
                print("Google Maps client initialized")
            except Exception as e:
                print(f"Failed to initialize Google Maps client: {e}")
                self.mock_mode = True
        else:
            print("Using mock navigation mode")
            self.mock_mode = True
    
    def set_callbacks(self, instruction_callback: Callable = None,
                     arrival_callback: Callable = None,
                     error_callback: Callable = None):
        """Set callback functions for navigation events."""
        self.instruction_callback = instruction_callback
        self.arrival_callback = arrival_callback
        self.error_callback = error_callback
    
    def start_navigation(self, destination_address: str, origin_address: str = None) -> bool:
        """Start navigation to a destination."""
        try:
            self.state = NavigationState.PLANNING
            
            # Resolve destination
            destination_location = self._resolve_address(destination_address)
            if not destination_location:
                self._handle_error(f"Could not resolve destination: {destination_address}")
                return False
            
            # Resolve origin (use current location if not provided)
            if origin_address:
                origin_location = self._resolve_address(origin_address)
                if not origin_location:
                    self._handle_error(f"Could not resolve origin: {origin_address}")
                    return False
            else:
                origin_location = self.current_location or self.mock_current_location
            
            # Plan route
            route = self._plan_route(origin_location, destination_location)
            if not route:
                self._handle_error("Could not plan route")
                return False
            
            # Start navigation
            with self.navigation_lock:
                self.current_route = route
                self.current_step_index = 0
                self.current_location = origin_location
                self.destination = destination_location
                self.is_navigating = True
                self.state = NavigationState.NAVIGATING
            
            # Start navigation thread
            self.navigation_thread = threading.Thread(target=self._navigation_loop)
            self.navigation_thread.daemon = True
            self.navigation_thread.start()
            
            # Give first instruction
            self._announce_instruction()
            
            return True
            
        except Exception as e:
            self._handle_error(f"Navigation start failed: {e}")
            return False
    
    def pause_navigation(self):
        """Pause the current navigation."""
        if self.state == NavigationState.NAVIGATING:
            self.state = NavigationState.PAUSED
            if self.instruction_callback:
                self.instruction_callback("Navigation paused")
    
    def resume_navigation(self):
        """Resume paused navigation."""
        if self.state == NavigationState.PAUSED:
            self.state = NavigationState.NAVIGATING
            self._announce_instruction()
    
    def stop_navigation(self):
        """Stop the current navigation."""
        self.is_navigating = False
        self.state = NavigationState.IDLE
        
        if self.navigation_thread:
            self.navigation_thread.join(timeout=2.0)
        
        if self.instruction_callback:
            self.instruction_callback("Navigation stopped")
    
    def next_instruction(self):
        """Manually request next instruction."""
        if self.state == NavigationState.NAVIGATING and self.current_route:
            with self.navigation_lock:
                if self.current_step_index < len(self.current_route) - 1:
                    self.current_step_index += 1
                    self._announce_instruction()
                else:
                    self._handle_arrival()
    
    def _resolve_address(self, address: str) -> Optional[Location]:
        """Resolve an address to GPS coordinates."""
        if self.mock_mode:
            return self._mock_resolve_address(address)
        
        try:
            geocode_result = self.gmaps_client.geocode(address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                return Location(
                    latitude=location['lat'],
                    longitude=location['lng'],
                    address=geocode_result[0]['formatted_address']
                )
        except Exception as e:
            print(f"Geocoding error: {e}")
        
        return None
    
    def _mock_resolve_address(self, address: str) -> Location:
        """Mock address resolution for simulation."""
        # Simple mock locations for common addresses
        mock_locations = {
            "home": Location(37.7749, -122.4194, "Home - San Francisco, CA"),
            "work": Location(37.7849, -122.4094, "Work - San Francisco, CA"),
            "store": Location(37.7649, -122.4294, "Store - San Francisco, CA"),
            "hospital": Location(37.7949, -122.3994, "Hospital - San Francisco, CA"),
            "library": Location(37.7549, -122.4394, "Library - San Francisco, CA"),
        }
        
        # Check for exact matches
        address_lower = address.lower()
        for key, location in mock_locations.items():
            if key in address_lower:
                return location
        
        # Generate mock location based on address hash
        import hashlib
        hash_value = int(hashlib.md5(address.encode()).hexdigest()[:8], 16)
        
        # Generate coordinates around San Francisco
        lat_offset = (hash_value % 1000) / 10000.0 - 0.05  # ±0.05 degrees
        lon_offset = ((hash_value // 1000) % 1000) / 10000.0 - 0.05
        
        return Location(
            latitude=37.7749 + lat_offset,
            longitude=-122.4194 + lon_offset,
            address=address
        )
    
    def _plan_route(self, origin: Location, destination: Location) -> Optional[List[RouteStep]]:
        """Plan a route between two locations."""
        if self.mock_mode:
            return self._mock_plan_route(origin, destination)
        
        try:
            directions_result = self.gmaps_client.directions(
                (origin.latitude, origin.longitude),
                (destination.latitude, destination.longitude),
                mode="walking"
            )
            
            if directions_result:
                return self._parse_directions(directions_result[0])
                
        except Exception as e:
            print(f"Route planning error: {e}")
        
        return None
    
    def _mock_plan_route(self, origin: Location, destination: Location) -> List[RouteStep]:
        """Generate a mock route for simulation."""
        distance = origin.distance_to(destination)
        num_steps = max(3, int(distance / 100))  # One step per ~100m
        
        steps = []
        
        # Calculate step-by-step waypoints
        lat_step = (destination.latitude - origin.latitude) / num_steps
        lon_step = (destination.longitude - origin.longitude) / num_steps
        
        instructions = [
            "Head north on Main Street",
            "Turn right on Oak Avenue",
            "Continue straight for 200 meters",
            "Turn left on Pine Street",
            "Your destination will be on the right"
        ]
        
        maneuvers = ["straight", "turn-right", "straight", "turn-left", "straight"]
        
        for i in range(num_steps):
            start_lat = origin.latitude + lat_step * i
            start_lon = origin.longitude + lon_step * i
            end_lat = origin.latitude + lat_step * (i + 1)
            end_lon = origin.longitude + lon_step * (i + 1)
            
            start_location = Location(start_lat, start_lon)
            end_location = Location(end_lat, end_lon)
            step_distance = start_location.distance_to(end_location)
            
            instruction = instructions[min(i, len(instructions) - 1)]
            maneuver = maneuvers[min(i, len(maneuvers) - 1)]
            
            if i == num_steps - 1:
                instruction = f"Arrive at {destination.address}"
                maneuver = "arrive"
            
            step = RouteStep(
                instruction=instruction,
                distance=step_distance,
                duration=step_distance / self.config["navigation_settings"]["walking_speed"],
                start_location=start_location,
                end_location=end_location,
                maneuver=maneuver
            )
            steps.append(step)
        
        return steps
    
    def _parse_directions(self, directions: Dict) -> List[RouteStep]:
        """Parse Google Directions API response into RouteStep objects."""
        steps = []
        
        for leg in directions['legs']:
            for step in leg['steps']:
                route_step = RouteStep(
                    instruction=step['html_instructions'],
                    distance=step['distance']['value'],  # meters
                    duration=step['duration']['value'],  # seconds
                    start_location=Location(
                        step['start_location']['lat'],
                        step['start_location']['lng']
                    ),
                    end_location=Location(
                        step['end_location']['lat'],
                        step['end_location']['lng']
                    ),
                    maneuver=step.get('maneuver', 'straight')
                )
                steps.append(route_step)
        
        return steps
    
    def _navigation_loop(self):
        """Main navigation loop running in separate thread."""
        while self.is_navigating and self.state != NavigationState.ARRIVED:
            try:
                if self.state == NavigationState.NAVIGATING:
                    # Simulate movement along the route
                    self._update_position()
                    
                    # Check if we should announce next instruction
                    if self._should_announce_next():
                        self.next_instruction()
                
                time.sleep(self.config["navigation_settings"]["route_update_interval"])
                
            except Exception as e:
                print(f"Navigation loop error: {e}")
                self._handle_error(f"Navigation error: {e}")
                break
    
    def _update_position(self):
        """Update current position (simulated)."""
        if not self.current_route or self.current_step_index >= len(self.current_route):
            return
        
        # In mock mode, simulate walking along the route
        if self.mock_mode:
            current_step = self.current_route[self.current_step_index]
            walking_speed = self.config["navigation_settings"]["walking_speed"]
            
            # Calculate how much we should have moved
            time_elapsed = 1.0  # Assume 1 second since last update
            distance_moved = walking_speed * time_elapsed
            
            # Move towards the end of current step
            if hasattr(self, '_step_progress'):
                self._step_progress += distance_moved
            else:
                self._step_progress = 0
            
            # Check if we've completed the current step
            if self._step_progress >= current_step.distance:
                self._step_progress = 0
                with self.navigation_lock:
                    self.current_location = current_step.end_location
    
    def _should_announce_next(self) -> bool:
        """Check if we should announce the next instruction."""
        if not self.current_route or self.current_step_index >= len(self.current_route):
            return False
        
        # In mock mode, advance every few seconds for demo
        if self.mock_mode:
            return hasattr(self, '_last_announcement') and \
                   time.time() - self._last_announcement > 3.0
        
        # In real mode, check distance to next turn
        current_step = self.current_route[self.current_step_index]
        announcement_distance = self.config["navigation_settings"]["turn_announcement_distance"]
        
        remaining_distance = current_step.distance - getattr(self, '_step_progress', 0)
        return remaining_distance <= announcement_distance
    
    def _announce_instruction(self):
        """Announce the current navigation instruction."""
        if not self.current_route or self.current_step_index >= len(self.current_route):
            return
        
        current_step = self.current_route[self.current_step_index]
        
        # Format instruction for voice
        instruction = self._format_instruction(current_step)
        
        if self.instruction_callback:
            self.instruction_callback(instruction)
        
        self._last_announcement = time.time()
        
        # Check if this was the last step
        if self.current_step_index == len(self.current_route) - 1:
            self._handle_arrival()
    
    def _format_instruction(self, step: RouteStep) -> str:
        """Format a route step into a voice-friendly instruction."""
        instruction = step.instruction
        
        # Clean up HTML tags (basic cleaning)
        import re
        instruction = re.sub('<.*?>', '', instruction)
        
        # Add distance information
        if step.distance > 1000:
            distance_str = f"{step.distance / 1000:.1f} kilometers"
        else:
            distance_str = f"{int(step.distance)} meters"
        
        # Format final instruction
        if "arrive" in instruction.lower():
            return f"You have arrived at your destination"
        else:
            direction = step.get_direction()
            if direction != "forward":
                return f"In {distance_str}, {instruction}"
            else:
                return f"Continue {distance_str}, then {instruction}"
    
    def _handle_arrival(self):
        """Handle arrival at destination."""
        self.state = NavigationState.ARRIVED
        self.is_navigating = False
        
        if self.arrival_callback:
            self.arrival_callback("You have arrived at your destination!")
    
    def _handle_error(self, error_message: str):
        """Handle navigation errors."""
        self.state = NavigationState.ERROR
        self.is_navigating = False
        
        if self.error_callback:
            self.error_callback(error_message)
        else:
            print(f"Navigation error: {error_message}")
    
    def get_navigation_status(self) -> Dict:
        """Get current navigation status."""
        status = {
            "state": self.state.value,
            "current_step": None,
            "steps_remaining": 0,
            "total_distance": 0,
            "estimated_time": 0,
            "progress_percentage": 0
        }
        
        if self.current_route:
            status["total_distance"] = sum(step.distance for step in self.current_route)
            status["estimated_time"] = sum(step.duration for step in self.current_route)
            status["steps_remaining"] = len(self.current_route) - self.current_step_index
            
            if self.current_step_index < len(self.current_route):
                status["current_step"] = {
                    "instruction": self.current_route[self.current_step_index].instruction,
                    "distance": self.current_route[self.current_step_index].distance,
                    "maneuver": self.current_route[self.current_step_index].maneuver
                }
            
            # Calculate progress
            completed_steps = self.current_step_index
            total_steps = len(self.current_route)
            status["progress_percentage"] = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        return status
    
    def get_route_overview(self) -> Optional[Dict]:
        """Get overview of the current route."""
        if not self.current_route:
            return None
        
        total_distance = sum(step.distance for step in self.current_route)
        total_time = sum(step.duration for step in self.current_route)
        
        return {
            "total_steps": len(self.current_route),
            "total_distance": total_distance,
            "total_time": total_time,
            "origin": self.current_location.address if self.current_location else "Unknown",
            "destination": self.destination.address if self.destination else "Unknown"
        }


# Example usage and testing
if __name__ == "__main__":
    import time
    
    def on_instruction(message):
        print(f"🗣️  INSTRUCTION: {message}")
    
    def on_arrival(message):
        print(f"🎯 ARRIVAL: {message}")
    
    def on_error(message):
        print(f"❌ ERROR: {message}")
    
    # Create navigation system
    nav_system = NavigationSystem()
    nav_system.set_callbacks(
        instruction_callback=on_instruction,
        arrival_callback=on_arrival,
        error_callback=on_error
    )
    
    try:
        # Start navigation
        print("Starting navigation to library...")
        success = nav_system.start_navigation("library", "home")
        
        if success:
            print("Navigation started successfully!")
            
            # Monitor navigation for 15 seconds
            start_time = time.time()
            while time.time() - start_time < 15 and nav_system.state != NavigationState.ARRIVED:
                status = nav_system.get_navigation_status()
                print(f"Status: {status['state']}, Progress: {status['progress_percentage']:.1f}%")
                time.sleep(2)
        
    finally:
        nav_system.stop_navigation()
        print("Navigation system stopped")