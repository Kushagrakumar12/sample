"""
Tests for the Navigation System module.
"""

import unittest
import time
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

from navigation_system import NavigationSystem, NavigationState, Location, RouteStep


class TestLocation(unittest.TestCase):
    """Test cases for Location class."""
    
    def test_location_creation(self):
        """Test location creation."""
        loc = Location(37.7749, -122.4194, "San Francisco")
        self.assertEqual(loc.latitude, 37.7749)
        self.assertEqual(loc.longitude, -122.4194)
        self.assertEqual(loc.address, "San Francisco")
    
    def test_distance_calculation(self):
        """Test distance calculation between locations."""
        loc1 = Location(37.7749, -122.4194)  # San Francisco
        loc2 = Location(37.7849, -122.4094)  # Nearby location
        
        distance = loc1.distance_to(loc2)
        self.assertGreater(distance, 0)
        self.assertLess(distance, 2000)  # Should be less than 2km


class TestRouteStep(unittest.TestCase):
    """Test cases for RouteStep class."""
    
    def test_route_step_creation(self):
        """Test route step creation."""
        start_loc = Location(37.7749, -122.4194)
        end_loc = Location(37.7849, -122.4094)
        
        step = RouteStep(
            instruction="Turn right on Main St",
            distance=100.0,
            duration=60.0,
            start_location=start_loc,
            end_location=end_loc,
            maneuver="turn-right"
        )
        
        self.assertEqual(step.instruction, "Turn right on Main St")
        self.assertEqual(step.distance, 100.0)
        self.assertEqual(step.duration, 60.0)
        self.assertEqual(step.maneuver, "turn-right")
    
    def test_direction_extraction(self):
        """Test direction extraction from maneuver."""
        step = RouteStep("", 0, 0, None, None, "turn-left")
        self.assertEqual(step.get_direction(), "left")
        
        step = RouteStep("", 0, 0, None, None, "turn-right")
        self.assertEqual(step.get_direction(), "right")
        
        step = RouteStep("", 0, 0, None, None, "continue")
        self.assertEqual(step.get_direction(), "straight")


class TestNavigationSystem(unittest.TestCase):
    """Test cases for NavigationSystem class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.nav_system = NavigationSystem()
    
    def tearDown(self):
        """Clean up after tests."""
        if self.nav_system.is_navigating:
            self.nav_system.stop_navigation()
    
    def test_initialization(self):
        """Test navigation system initialization."""
        self.assertIsNotNone(self.nav_system)
        self.assertEqual(self.nav_system.state, NavigationState.IDLE)
        self.assertFalse(self.nav_system.is_navigating)
    
    def test_mock_address_resolution(self):
        """Test mock address resolution."""
        # Test known addresses
        home_loc = self.nav_system._mock_resolve_address("home")
        self.assertIsInstance(home_loc, Location)
        self.assertEqual(home_loc.address, "Home - San Francisco, CA")
        
        work_loc = self.nav_system._mock_resolve_address("work")
        self.assertIsInstance(work_loc, Location)
        
        # Test unknown address (should still return a location)
        unknown_loc = self.nav_system._mock_resolve_address("unknown place")
        self.assertIsInstance(unknown_loc, Location)
    
    def test_mock_route_planning(self):
        """Test mock route planning."""
        origin = Location(37.7749, -122.4194, "Origin")
        destination = Location(37.7849, -122.4094, "Destination")
        
        route = self.nav_system._mock_plan_route(origin, destination)
        self.assertIsInstance(route, list)
        self.assertGreater(len(route), 0)
        
        # Test route step structure
        for step in route:
            self.assertIsInstance(step, RouteStep)
            self.assertIsInstance(step.instruction, str)
            self.assertGreater(step.distance, 0)
            self.assertGreater(step.duration, 0)
    
    def test_navigation_start_stop(self):
        """Test starting and stopping navigation."""
        # Test successful start
        success = self.nav_system.start_navigation("library")
        self.assertTrue(success)
        self.assertEqual(self.nav_system.state, NavigationState.NAVIGATING)
        
        # Test stop
        self.nav_system.stop_navigation()
        self.assertEqual(self.nav_system.state, NavigationState.IDLE)
        self.assertFalse(self.nav_system.is_navigating)
    
    def test_navigation_pause_resume(self):
        """Test pausing and resuming navigation."""
        # Start navigation first
        self.nav_system.start_navigation("work")
        
        # Test pause
        self.nav_system.pause_navigation()
        self.assertEqual(self.nav_system.state, NavigationState.PAUSED)
        
        # Test resume
        self.nav_system.resume_navigation()
        self.assertEqual(self.nav_system.state, NavigationState.NAVIGATING)
    
    def test_navigation_status(self):
        """Test navigation status reporting."""
        # Test idle status
        status = self.nav_system.get_navigation_status()
        self.assertEqual(status['state'], 'idle')
        self.assertEqual(status['progress_percentage'], 0)
        
        # Test navigation status
        self.nav_system.start_navigation("store")
        status = self.nav_system.get_navigation_status()
        self.assertEqual(status['state'], 'navigating')
        self.assertIsNotNone(status['current_step'])
    
    def test_route_overview(self):
        """Test route overview generation."""
        # No route initially
        overview = self.nav_system.get_route_overview()
        self.assertIsNone(overview)
        
        # Start navigation and check overview
        self.nav_system.start_navigation("library")
        overview = self.nav_system.get_route_overview()
        
        self.assertIsNotNone(overview)
        self.assertIn('total_steps', overview)
        self.assertIn('total_distance', overview)
        self.assertIn('total_time', overview)
        self.assertGreater(overview['total_steps'], 0)
    
    def test_instruction_formatting(self):
        """Test instruction formatting for voice output."""
        start_loc = Location(37.7749, -122.4194)
        end_loc = Location(37.7849, -122.4094)
        
        step = RouteStep(
            instruction="Turn right on Oak Street",
            distance=150.0,
            duration=90.0,
            start_location=start_loc,
            end_location=end_loc,
            maneuver="turn-right"
        )
        
        formatted = self.nav_system._format_instruction(step)
        self.assertIsInstance(formatted, str)
        self.assertIn("150", formatted)  # Should include distance
    
    def test_callbacks(self):
        """Test navigation callbacks."""
        instruction_called = []
        arrival_called = []
        error_called = []
        
        def on_instruction(msg):
            instruction_called.append(msg)
        
        def on_arrival(msg):
            arrival_called.append(msg)
        
        def on_error(msg):
            error_called.append(msg)
        
        # Set callbacks
        self.nav_system.set_callbacks(on_instruction, on_arrival, on_error)
        
        # Start navigation (should trigger instruction callback)
        self.nav_system.start_navigation("hospital")
        time.sleep(0.1)  # Allow callback to execute
        
        # Check that instruction callback was called
        self.assertGreater(len(instruction_called), 0)


class TestNavigationIntegration(unittest.TestCase):
    """Integration tests for NavigationSystem."""
    
    def test_complete_navigation_cycle(self):
        """Test a complete navigation cycle."""
        nav_system = NavigationSystem()
        
        try:
            # Start navigation
            success = nav_system.start_navigation("library", "home")
            self.assertTrue(success)
            
            # Let it run for a bit
            time.sleep(1.0)
            
            # Check status
            status = nav_system.get_navigation_status()
            self.assertEqual(status['state'], 'navigating')
            
            # Simulate next instruction
            nav_system.next_instruction()
            
            # Pause and resume
            nav_system.pause_navigation()
            self.assertEqual(nav_system.get_navigation_status()['state'], 'paused')
            
            nav_system.resume_navigation()
            self.assertEqual(nav_system.get_navigation_status()['state'], 'navigating')
            
        finally:
            nav_system.stop_navigation()
    
    def test_navigation_with_invalid_destination(self):
        """Test navigation with various destination formats."""
        nav_system = NavigationSystem()
        
        try:
            # Test empty destination
            success = nav_system.start_navigation("")
            self.assertFalse(success)
            
            # Test valid destination
            success = nav_system.start_navigation("valid destination")
            self.assertTrue(success)
            
        finally:
            nav_system.stop_navigation()


if __name__ == '__main__':
    unittest.main()