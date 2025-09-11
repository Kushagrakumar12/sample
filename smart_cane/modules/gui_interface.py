"""
Module 4: GUI Interface

This module provides a modern Tkinter-based graphical user interface
for the smart cane system with real-time camera feed, controls, and status monitoring.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import os
from typing import Dict, List, Optional, Callable
import cv2
import numpy as np
from PIL import Image, ImageTk
from datetime import datetime


class SmartCaneGUI:
    """
    Modern graphical user interface for the Smart Cane system.
    Provides real-time camera feed, navigation controls, and system monitoring.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the GUI interface."""
        self.config = self._load_config(config_path)
        
        # Main window
        self.root = tk.Tk()
        self.root.title("Smart Cane Control System")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # GUI state
        self.is_running = False
        self.camera_thread = None
        self.status_thread = None
        
        # Camera and video
        self.current_frame = None
        self.camera_label = None
        self.video_canvas = None
        
        # System components (will be injected)
        self.obstacle_detector = None
        self.navigation_system = None
        self.voice_system = None
        
        # GUI components
        self.status_vars = {}
        self.control_buttons = {}
        self.log_text = None
        
        # Create GUI layout
        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()
        
        # Configure window behavior
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def _load_config(self, config_path: str) -> Dict:
        """Load GUI configuration."""
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "gui_settings": {
                "window_width": 1200,
                "window_height": 800,
                "theme": "light",
                "font_size": 12,
                "accessibility_mode": True
            }
        }
    
    def _create_menu(self):
        """Create the main menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Settings", command=self._save_settings)
        file_menu.add_command(label="Load Settings", command=self._load_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # System menu
        system_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="System", menu=system_menu)
        system_menu.add_command(label="Start All Systems", command=self._start_all_systems)
        system_menu.add_command(label="Stop All Systems", command=self._stop_all_systems)
        system_menu.add_separator()
        system_menu.add_command(label="Emergency Test", command=self._test_emergency)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Voice Settings", command=self._open_voice_settings)
        settings_menu.add_command(label="Detection Settings", command=self._open_detection_settings)
        settings_menu.add_command(label="Navigation Settings", command=self._open_navigation_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self._show_help)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_main_layout(self):
        """Create the main GUI layout."""
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Left panel - Camera and detection
        self._create_camera_panel(main_frame)
        
        # Right panel - Controls and status
        self._create_control_panel(main_frame)
    
    def _create_camera_panel(self, parent):
        """Create the camera and detection panel."""
        # Camera frame
        camera_frame = ttk.LabelFrame(parent, text="Camera Feed & Detection", padding="10")
        camera_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        camera_frame.columnconfigure(0, weight=1)
        camera_frame.rowconfigure(0, weight=1)
        
        # Video canvas
        self.video_canvas = tk.Canvas(
            camera_frame,
            width=640,
            height=480,
            bg='black',
            highlightthickness=1,
            highlightbackground='gray'
        )
        self.video_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Camera controls
        camera_controls = ttk.Frame(camera_frame)
        camera_controls.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        camera_controls.columnconfigure(1, weight=1)
        
        # Camera control buttons
        self.control_buttons['start_camera'] = ttk.Button(
            camera_controls, text="Start Camera", command=self._toggle_camera
        )
        self.control_buttons['start_camera'].grid(row=0, column=0, padx=(0, 10))
        
        self.control_buttons['take_photo'] = ttk.Button(
            camera_controls, text="Take Photo", command=self._take_photo
        )
        self.control_buttons['take_photo'].grid(row=0, column=1, padx=(0, 10))
        
        # Detection status
        detection_status = ttk.Frame(camera_controls)
        detection_status.grid(row=0, column=2, sticky=(tk.E))
        
        ttk.Label(detection_status, text="Detection:").grid(row=0, column=0)
        self.status_vars['detection_status'] = tk.StringVar(value="Stopped")
        ttk.Label(
            detection_status, 
            textvariable=self.status_vars['detection_status'],
            foreground='red'
        ).grid(row=0, column=1, padx=(5, 0))
    
    def _create_control_panel(self, parent):
        """Create the control and status panel."""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        control_frame.columnconfigure(0, weight=1)
        control_frame.rowconfigure(2, weight=1)  # Log area gets extra space
        
        # Navigation controls
        self._create_navigation_controls(control_frame)
        
        # System status
        self._create_system_status(control_frame)
        
        # Log area
        self._create_log_area(control_frame)
        
        # Emergency controls
        self._create_emergency_controls(control_frame)
    
    def _create_navigation_controls(self, parent):
        """Create navigation control section."""
        nav_frame = ttk.LabelFrame(parent, text="Navigation Controls", padding="10")
        nav_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        nav_frame.columnconfigure(1, weight=1)
        
        # Destination entry
        ttk.Label(nav_frame, text="Destination:").grid(row=0, column=0, sticky=tk.W)
        self.destination_var = tk.StringVar(value="library")
        destination_entry = ttk.Entry(nav_frame, textvariable=self.destination_var)
        destination_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10))
        
        # Navigation buttons
        nav_buttons = ttk.Frame(nav_frame)
        nav_buttons.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        self.control_buttons['start_nav'] = ttk.Button(
            nav_buttons, text="Start Navigation", command=self._start_navigation
        )
        self.control_buttons['start_nav'].grid(row=0, column=0, padx=(0, 5))
        
        self.control_buttons['pause_nav'] = ttk.Button(
            nav_buttons, text="Pause", command=self._pause_navigation, state='disabled'
        )
        self.control_buttons['pause_nav'].grid(row=0, column=1, padx=5)
        
        self.control_buttons['stop_nav'] = ttk.Button(
            nav_buttons, text="Stop", command=self._stop_navigation, state='disabled'
        )
        self.control_buttons['stop_nav'].grid(row=0, column=2, padx=5)
        
        self.control_buttons['next_instruction'] = ttk.Button(
            nav_buttons, text="Next", command=self._next_instruction, state='disabled'
        )
        self.control_buttons['next_instruction'].grid(row=0, column=3, padx=(5, 0))
        
        # Navigation status
        nav_status = ttk.Frame(nav_frame)
        nav_status.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Label(nav_status, text="Status:").grid(row=0, column=0, sticky=tk.W)
        self.status_vars['nav_status'] = tk.StringVar(value="Idle")
        ttk.Label(nav_status, textvariable=self.status_vars['nav_status']).grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0)
        )
        
        ttk.Label(nav_status, text="Progress:").grid(row=1, column=0, sticky=tk.W)
        self.status_vars['nav_progress'] = tk.StringVar(value="0%")
        ttk.Label(nav_status, textvariable=self.status_vars['nav_progress']).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0)
        )
    
    def _create_system_status(self, parent):
        """Create system status section."""
        status_frame = ttk.LabelFrame(parent, text="System Status", padding="10")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Voice system status
        ttk.Label(status_frame, text="Voice System:").grid(row=0, column=0, sticky=tk.W)
        self.status_vars['voice_status'] = tk.StringVar(value="Stopped")
        ttk.Label(status_frame, textvariable=self.status_vars['voice_status']).grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0)
        )
        
        # Detection count
        ttk.Label(status_frame, text="Objects Detected:").grid(row=1, column=0, sticky=tk.W)
        self.status_vars['detection_count'] = tk.StringVar(value="0")
        ttk.Label(status_frame, textvariable=self.status_vars['detection_count']).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0)
        )
        
        # Alerts count
        ttk.Label(status_frame, text="Active Alerts:").grid(row=2, column=0, sticky=tk.W)
        self.status_vars['alerts_count'] = tk.StringVar(value="0")
        ttk.Label(status_frame, textvariable=self.status_vars['alerts_count']).grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0)
        )
        
        # System controls
        system_buttons = ttk.Frame(status_frame)
        system_buttons.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        self.control_buttons['start_system'] = ttk.Button(
            system_buttons, text="Start All", command=self._start_all_systems
        )
        self.control_buttons['start_system'].grid(row=0, column=0, padx=(0, 5))
        
        self.control_buttons['stop_system'] = ttk.Button(
            system_buttons, text="Stop All", command=self._stop_all_systems
        )
        self.control_buttons['stop_system'].grid(row=0, column=1, padx=5)
        
        # Volume control
        volume_frame = ttk.Frame(status_frame)
        volume_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Label(volume_frame, text="Volume:").grid(row=0, column=0, sticky=tk.W)
        self.volume_var = tk.DoubleVar(value=0.8)
        volume_scale = ttk.Scale(
            volume_frame, from_=0.0, to=1.0, orient=tk.HORIZONTAL,
            variable=self.volume_var, command=self._on_volume_change
        )
        volume_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        volume_frame.columnconfigure(1, weight=1)
    
    def _create_log_area(self, parent):
        """Create the log display area."""
        log_frame = ttk.LabelFrame(parent, text="System Log", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Create text widget with scrollbar
        text_frame = ttk.Frame(log_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(
            text_frame,
            height=10,
            width=50,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#f8f8f8'
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Log control buttons
        log_controls = ttk.Frame(log_frame)
        log_controls.grid(row=1, column=0, pady=(10, 0))
        
        ttk.Button(log_controls, text="Clear Log", command=self._clear_log).grid(row=0, column=0)
        ttk.Button(log_controls, text="Save Log", command=self._save_log).grid(row=0, column=1, padx=(10, 0))
    
    def _create_emergency_controls(self, parent):
        """Create emergency control section."""
        emergency_frame = ttk.LabelFrame(parent, text="Emergency Controls", padding="10")
        emergency_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        emergency_frame.columnconfigure(0, weight=1)
        
        # Emergency button (large and prominent)
        self.control_buttons['emergency'] = tk.Button(
            emergency_frame,
            text="🚨 EMERGENCY 🚨",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='red',
            activebackground='darkred',
            command=self._trigger_emergency,
            height=2
        )
        self.control_buttons['emergency'].grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Emergency status
        self.status_vars['emergency_status'] = tk.StringVar(value="Ready")
        ttk.Label(
            emergency_frame,
            textvariable=self.status_vars['emergency_status'],
            font=('Arial', 10, 'bold')
        ).grid(row=1, column=0)
    
    def _create_status_bar(self):
        """Create the status bar at the bottom."""
        status_bar = ttk.Frame(self.root)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        status_bar.columnconfigure(0, weight=1)
        
        # Status text
        self.status_vars['main_status'] = tk.StringVar(value="Ready - Smart Cane System")
        ttk.Label(status_bar, textvariable=self.status_vars['main_status']).grid(
            row=0, column=0, sticky=tk.W, padx=10
        )
        
        # Time display
        self.status_vars['time_status'] = tk.StringVar()
        ttk.Label(status_bar, textvariable=self.status_vars['time_status']).grid(
            row=0, column=1, sticky=tk.E, padx=10
        )
        
        # Update time every second
        self._update_time()
    
    def set_system_components(self, obstacle_detector=None, navigation_system=None, voice_system=None):
        """Set references to system components."""
        self.obstacle_detector = obstacle_detector
        self.navigation_system = navigation_system
        self.voice_system = voice_system
    
    def start(self):
        """Start the GUI and all background processes."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start status update thread
        self.status_thread = threading.Thread(target=self._status_update_loop)
        self.status_thread.daemon = True
        self.status_thread.start()
        
        # Log startup
        self.log_message("Smart Cane GUI started", "INFO")
        
        # Run the GUI
        self.root.mainloop()
    
    def stop(self):
        """Stop the GUI and all processes."""
        self.is_running = False
        
        # Stop all systems
        self._stop_all_systems()
        
        # Wait for threads to finish
        if self.camera_thread:
            self.camera_thread.join(timeout=1.0)
        
        if self.status_thread:
            self.status_thread.join(timeout=1.0)
    
    def on_closing(self):
        """Handle window closing event."""
        if messagebox.askokcancel("Quit", "Do you want to quit the Smart Cane system?"):
            self.stop()
            self.root.destroy()
    
    def _toggle_camera(self):
        """Toggle camera feed on/off."""
        if self.camera_thread and self.camera_thread.is_alive():
            self._stop_camera()
        else:
            self._start_camera()
    
    def _start_camera(self):
        """Start camera feed."""
        if self.camera_thread and self.camera_thread.is_alive():
            return
        
        self.camera_thread = threading.Thread(target=self._camera_loop)
        self.camera_thread.daemon = True
        self.camera_thread.start()
        
        self.control_buttons['start_camera'].config(text="Stop Camera")
        self.status_vars['detection_status'].set("Running")
        self.log_message("Camera started", "INFO")
    
    def _stop_camera(self):
        """Stop camera feed."""
        if self.camera_thread:
            # Camera thread will stop when is_running is False
            pass
        
        self.control_buttons['start_camera'].config(text="Start Camera")
        self.status_vars['detection_status'].set("Stopped")
        self.log_message("Camera stopped", "INFO")
        
        # Clear camera display
        self.video_canvas.delete("all")
        self.video_canvas.create_text(320, 240, text="Camera Stopped", fill="white", font=('Arial', 16))
    
    def _camera_loop(self):
        """Camera processing loop."""
        while self.is_running:
            try:
                if self.obstacle_detector:
                    # Get frame with detections
                    frame = self.obstacle_detector.get_annotated_frame()
                    if frame is not None:
                        self._display_frame(frame)
                else:
                    # Show placeholder if no detector
                    self._show_camera_placeholder()
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                self.log_message(f"Camera error: {e}", "ERROR")
                time.sleep(1.0)
    
    def _display_frame(self, frame):
        """Display a frame in the video canvas."""
        try:
            # Resize frame to fit canvas
            height, width = frame.shape[:2]
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                # Calculate scaling to fit canvas while maintaining aspect ratio
                scale_x = canvas_width / width
                scale_y = canvas_height / height
                scale = min(scale_x, scale_y)
                
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                resized_frame = cv2.resize(frame, (new_width, new_height))
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                
                # Convert to PIL Image
                pil_image = Image.fromarray(rgb_frame)
                
                # Convert to Tkinter PhotoImage
                tk_image = ImageTk.PhotoImage(pil_image)
                
                # Display on canvas
                self.video_canvas.delete("all")
                self.video_canvas.create_image(
                    canvas_width // 2, canvas_height // 2,
                    image=tk_image
                )
                
                # Keep a reference to prevent garbage collection
                self.video_canvas.image = tk_image
        
        except Exception as e:
            print(f"Display frame error: {e}")
    
    def _show_camera_placeholder(self):
        """Show placeholder when camera is not available."""
        self.video_canvas.delete("all")
        self.video_canvas.create_rectangle(0, 0, 640, 480, fill="black")
        self.video_canvas.create_text(
            320, 240, text="Camera Feed\n(Simulated Mode)",
            fill="white", font=('Arial', 16), justify=tk.CENTER
        )
    
    def _start_navigation(self):
        """Start navigation to destination."""
        destination = self.destination_var.get().strip()
        if not destination:
            messagebox.showwarning("Warning", "Please enter a destination")
            return
        
        if self.navigation_system:
            success = self.navigation_system.start_navigation(destination)
            if success:
                self.control_buttons['start_nav'].config(state='disabled')
                self.control_buttons['pause_nav'].config(state='normal')
                self.control_buttons['stop_nav'].config(state='normal')
                self.control_buttons['next_instruction'].config(state='normal')
                
                self.log_message(f"Navigation started to: {destination}", "INFO")
            else:
                self.log_message("Failed to start navigation", "ERROR")
        else:
            self.log_message("Navigation system not available", "WARNING")
    
    def _pause_navigation(self):
        """Pause/resume navigation."""
        if self.navigation_system:
            status = self.navigation_system.get_navigation_status()
            if status['state'] == 'navigating':
                self.navigation_system.pause_navigation()
                self.control_buttons['pause_nav'].config(text="Resume")
                self.log_message("Navigation paused", "INFO")
            elif status['state'] == 'paused':
                self.navigation_system.resume_navigation()
                self.control_buttons['pause_nav'].config(text="Pause")
                self.log_message("Navigation resumed", "INFO")
    
    def _stop_navigation(self):
        """Stop navigation."""
        if self.navigation_system:
            self.navigation_system.stop_navigation()
            
            self.control_buttons['start_nav'].config(state='normal')
            self.control_buttons['pause_nav'].config(state='disabled', text="Pause")
            self.control_buttons['stop_nav'].config(state='disabled')
            self.control_buttons['next_instruction'].config(state='disabled')
            
            self.log_message("Navigation stopped", "INFO")
    
    def _next_instruction(self):
        """Get next navigation instruction."""
        if self.navigation_system:
            self.navigation_system.next_instruction()
    
    def _start_all_systems(self):
        """Start all system components."""
        self.log_message("Starting all systems...", "INFO")
        
        # Start obstacle detector
        if self.obstacle_detector:
            self.obstacle_detector.start_detection(use_mock=True)
            self.log_message("Obstacle detection started", "INFO")
        
        # Start voice system
        if self.voice_system:
            self.voice_system.start()
            self.log_message("Voice system started", "INFO")
        
        # Start camera
        self._start_camera()
        
        self.status_vars['main_status'].set("All systems running")
    
    def _stop_all_systems(self):
        """Stop all system components."""
        self.log_message("Stopping all systems...", "INFO")
        
        # Stop navigation
        self._stop_navigation()
        
        # Stop camera
        self._stop_camera()
        
        # Stop obstacle detector
        if self.obstacle_detector:
            self.obstacle_detector.stop_detection()
            self.log_message("Obstacle detection stopped", "INFO")
        
        # Stop voice system
        if self.voice_system:
            self.voice_system.stop()
            self.log_message("Voice system stopped", "INFO")
        
        self.status_vars['main_status'].set("All systems stopped")
    
    def _trigger_emergency(self):
        """Trigger emergency alert."""
        if self.voice_system:
            self.voice_system.trigger_emergency_alert("Current GPS Location")
            self.status_vars['emergency_status'].set("🚨 EMERGENCY ACTIVE 🚨")
            self.log_message("EMERGENCY ALERT TRIGGERED", "EMERGENCY")
        else:
            messagebox.showinfo("Emergency", "Emergency alert would be triggered!\n(Voice system not available)")
    
    def _test_emergency(self):
        """Test emergency system."""
        result = messagebox.askyesno("Emergency Test", "Test the emergency alert system?")
        if result:
            self._trigger_emergency()
    
    def _on_volume_change(self, value):
        """Handle volume slider change."""
        volume = float(value)
        if self.voice_system:
            self.voice_system.set_volume(volume)
        self.log_message(f"Volume set to {volume:.2f}", "INFO")
    
    def _take_photo(self):
        """Take a photo of current camera feed."""
        if self.obstacle_detector:
            frame = self.obstacle_detector.get_current_frame()
            if frame is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"smart_cane_photo_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                self.log_message(f"Photo saved: {filename}", "INFO")
                messagebox.showinfo("Photo Saved", f"Photo saved as {filename}")
            else:
                messagebox.showwarning("Warning", "No camera feed available")
        else:
            messagebox.showwarning("Warning", "Camera system not available")
    
    def _status_update_loop(self):
        """Update system status continuously."""
        while self.is_running:
            try:
                self._update_system_status()
                time.sleep(1.0)
            except Exception as e:
                print(f"Status update error: {e}")
    
    def _update_system_status(self):
        """Update all status displays."""
        # Update detection status
        if self.obstacle_detector:
            detections = self.obstacle_detector.get_current_detections()
            alerts = self.obstacle_detector.get_priority_alerts()
            
            self.status_vars['detection_count'].set(str(len(detections)))
            self.status_vars['alerts_count'].set(str(len(alerts)))
        
        # Update navigation status
        if self.navigation_system:
            nav_status = self.navigation_system.get_navigation_status()
            self.status_vars['nav_status'].set(nav_status['state'].title())
            self.status_vars['nav_progress'].set(f"{nav_status['progress_percentage']:.1f}%")
        
        # Update voice system status
        if self.voice_system:
            voice_status = self.voice_system.get_system_status()
            status_text = "Running" if voice_status['is_running'] else "Stopped"
            if voice_status['is_speaking']:
                status_text += " (Speaking)"
            self.status_vars['voice_status'].set(status_text)
    
    def _update_time(self):
        """Update time display."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_vars['time_status'].set(current_time)
        self.root.after(1000, self._update_time)
    
    def log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        # Add to text widget
        self.log_text.insert(tk.END, log_entry)
        
        # Color coding
        if level == "ERROR":
            self.log_text.tag_add("error", "end-2c linestart", "end-1c")
            self.log_text.tag_config("error", foreground="red")
        elif level == "WARNING":
            self.log_text.tag_add("warning", "end-2c linestart", "end-1c")
            self.log_text.tag_config("warning", foreground="orange")
        elif level == "EMERGENCY":
            self.log_text.tag_add("emergency", "end-2c linestart", "end-1c")
            self.log_text.tag_config("emergency", foreground="red", background="yellow")
        
        # Auto-scroll to bottom
        self.log_text.see(tk.END)
        
        # Limit log size (keep last 1000 lines)
        lines = self.log_text.get("1.0", tk.END).count('\n')
        if lines > 1000:
            self.log_text.delete("1.0", "2.0")
    
    def _clear_log(self):
        """Clear the log display."""
        self.log_text.delete("1.0", tk.END)
        self.log_message("Log cleared", "INFO")
    
    def _save_log(self):
        """Save log to file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Log File"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get("1.0", tk.END))
                self.log_message(f"Log saved to {filename}", "INFO")
            except Exception as e:
                self.log_message(f"Error saving log: {e}", "ERROR")
    
    def _save_settings(self):
        """Save current settings."""
        messagebox.showinfo("Settings", "Settings save functionality would be implemented here")
    
    def _load_settings(self):
        """Load settings from file."""
        messagebox.showinfo("Settings", "Settings load functionality would be implemented here")
    
    def _open_voice_settings(self):
        """Open voice settings dialog."""
        messagebox.showinfo("Voice Settings", "Voice settings dialog would open here")
    
    def _open_detection_settings(self):
        """Open detection settings dialog."""
        messagebox.showinfo("Detection Settings", "Detection settings dialog would open here")
    
    def _open_navigation_settings(self):
        """Open navigation settings dialog."""
        messagebox.showinfo("Navigation Settings", "Navigation settings dialog would open here")
    
    def _show_help(self):
        """Show help information."""
        help_text = """
Smart Cane Control System - User Guide

NAVIGATION:
1. Enter destination in the text field
2. Click 'Start Navigation' to begin route guidance
3. Use Pause/Resume to control navigation
4. Click 'Next' for the next instruction

CAMERA & DETECTION:
1. Click 'Start Camera' to begin obstacle detection
2. Detected objects will be highlighted with bounding boxes
3. Distance and confidence information is displayed

EMERGENCY:
1. Click the red EMERGENCY button for immediate help
2. Emergency contacts will be automatically notified
3. Your location will be shared with emergency services

CONTROLS:
- Volume slider adjusts voice feedback volume
- System log shows all activities and alerts
- Use menu options for advanced settings
        """
        
        messagebox.showinfo("User Guide", help_text)
    
    def _show_about(self):
        """Show about information."""
        about_text = """
Smart Cane Control System v1.0

A comprehensive navigation and safety system for visually impaired users.

Features:
• Real-time obstacle detection using computer vision
• Turn-by-turn voice navigation
• Emergency alert system
• Customizable voice feedback
• Modern graphical interface

Developed for accessibility and independence.
        """
        
        messagebox.showinfo("About Smart Cane System", about_text)


# Example usage
if __name__ == "__main__":
    # Create and start GUI
    gui = SmartCaneGUI()
    
    try:
        gui.start()
    except KeyboardInterrupt:
        print("GUI interrupted by user")
    finally:
        gui.stop()