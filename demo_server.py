#!/usr/bin/env python3
"""
AI-Powered Train Traffic Control System - Demo Server
A simplified version that demonstrates core functionality using only built-in Python libraries
"""

import http.server
import socketserver
import json
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
import threading
import time
import random
import os

# Database setup
def init_database():
    """Initialize SQLite database with sample data"""
    conn = sqlite3.connect('train_control_demo.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trains (
            id INTEGER PRIMARY KEY,
            number TEXT UNIQUE,
            name TEXT,
            train_type TEXT,
            priority TEXT,
            max_speed_kmh INTEGER,
            is_active BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            start_station TEXT,
            end_station TEXT,
            length_km REAL,
            max_speed_kmh INTEGER,
            capacity INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY,
            train_id INTEGER,
            track_id INTEGER,
            scheduled_departure TIMESTAMP,
            scheduled_arrival TIMESTAMP,
            status TEXT DEFAULT 'scheduled',
            delay_minutes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (train_id) REFERENCES trains (id),
            FOREIGN KEY (track_id) REFERENCES tracks (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS train_positions (
            id INTEGER PRIMARY KEY,
            train_id INTEGER,
            track_id INTEGER,
            position_km REAL,
            speed_kmh REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (train_id) REFERENCES trains (id),
            FOREIGN KEY (track_id) REFERENCES tracks (id)
        )
    ''')
    
    # Insert sample data if tables are empty
    cursor.execute('SELECT COUNT(*) FROM trains')
    if cursor.fetchone()[0] == 0:
        # Sample trains
        trains_data = [
            ('T001', 'Express Morning', 'express', 'high', 180, 1),
            ('T002', 'Local Commuter', 'passenger', 'medium', 120, 1),
            ('F001', 'Freight Heavy', 'freight', 'low', 80, 1),
            ('T003', 'Evening Express', 'express', 'high', 180, 1),
            ('L001', 'Local Service', 'local', 'medium', 100, 1)
        ]
        
        cursor.executemany('''
            INSERT INTO trains (number, name, train_type, priority, max_speed_kmh, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', trains_data)
        
        # Sample tracks
        tracks_data = [
            ('Main Line A', 'Central Station', 'North Terminal', 85.5, 160, 2),
            ('Express Route B', 'Central Station', 'East Junction', 120.0, 200, 1),
            ('Freight Line C', 'Industrial Hub', 'Port Terminal', 65.3, 80, 1),
            ('Local Route D', 'Suburban Center', 'Downtown', 45.2, 100, 3)
        ]
        
        cursor.executemany('''
            INSERT INTO tracks (name, start_station, end_station, length_km, max_speed_kmh, capacity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', tracks_data)
        
        # Sample schedules
        now = datetime.now()
        schedules_data = []
        for i in range(5):
            dep_time = now + timedelta(hours=i, minutes=random.randint(0, 59))
            arr_time = dep_time + timedelta(hours=random.randint(1, 3))
            schedules_data.append((
                i + 1,  # train_id
                (i % 4) + 1,  # track_id
                dep_time.isoformat(),
                arr_time.isoformat(),
                'scheduled'
            ))
        
        cursor.executemany('''
            INSERT INTO schedules (train_id, track_id, scheduled_departure, scheduled_arrival, status)
            VALUES (?, ?, ?, ?, ?)
        ''', schedules_data)
    
    conn.commit()
    return conn

class TrainControlHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for the train control system API"""
    
    def __init__(self, *args, db_conn=None, **kwargs):
        self.db_conn = db_conn
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/':
            self.serve_dashboard()
        elif path == '/api/trains':
            self.get_trains()
        elif path == '/api/tracks':
            self.get_tracks()
        elif path == '/api/schedules':
            self.get_schedules()
        elif path == '/api/status':
            self.get_system_status()
        elif path == '/api/analytics':
            self.get_analytics()
        elif path.startswith('/api/optimization'):
            self.run_optimization()
        else:
            self.send_error(404, "Not Found")
    
    def serve_dashboard(self):
        """Serve the main dashboard HTML"""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚆 AI Train Traffic Control System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header h1 { color: #1976d2; margin-bottom: 10px; }
        .metrics { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; 
            margin-bottom: 20px; 
        }
        .metric-card { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metric-value { 
            font-size: 2.5rem; 
            font-weight: bold; 
            color: #1976d2; 
            margin-bottom: 5px;
        }
        .metric-label { color: #666; }
        .data-section { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .data-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        .data-table th, .data-table td { 
            padding: 12px; 
            text-align: left; 
            border-bottom: 1px solid #eee; 
        }
        .data-table th { background: #f5f5f5; font-weight: 600; }
        .status-badge { 
            padding: 4px 8px; 
            border-radius: 12px; 
            font-size: 0.8rem; 
            font-weight: 500;
        }
        .status-scheduled { background: #e3f2fd; color: #1976d2; }
        .status-running { background: #e8f5e8; color: #4caf50; }
        .status-delayed { background: #fff3e0; color: #ff9800; }
        .priority-high { background: #ffebee; color: #f44336; }
        .priority-medium { background: #fff3e0; color: #ff9800; }
        .priority-low { background: #e8f5e8; color: #4caf50; }
        .refresh-btn { 
            background: #1976d2; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer;
            margin-bottom: 10px;
        }
        .refresh-btn:hover { background: #1565c0; }
        .real-time-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #4caf50;
            border-radius: 50%;
            margin-right: 5px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚆 AI-Powered Train Traffic Control System</h1>
            <p><span class="real-time-indicator"></span>Real-time Railway Operations Management & Optimization</p>
        </div>
        
        <div class="metrics" id="metrics">
            <!-- Metrics will be loaded here -->
        </div>
        
        <div class="data-section">
            <h2>Active Trains</h2>
            <button class="refresh-btn" onclick="loadData()">🔄 Refresh Data</button>
            <table class="data-table" id="trains-table">
                <thead>
                    <tr>
                        <th>Train Number</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Priority</th>
                        <th>Max Speed</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="trains-data">
                    <!-- Train data will be loaded here -->
                </tbody>
            </table>
        </div>
        
        <div class="data-section">
            <h2>Current Schedules</h2>
            <button class="refresh-btn" onclick="runOptimization()">⚡ Run AI Optimization</button>
            <table class="data-table" id="schedules-table">
                <thead>
                    <tr>
                        <th>Train</th>
                        <th>Route</th>
                        <th>Departure</th>
                        <th>Arrival</th>
                        <th>Status</th>
                        <th>Delay</th>
                    </tr>
                </thead>
                <tbody id="schedules-data">
                    <!-- Schedule data will be loaded here -->
                </tbody>
            </table>
        </div>
    </div>

    <script>
        async function loadData() {
            try {
                // Load metrics
                const statusResponse = await fetch('/api/status');
                const statusData = await statusResponse.json();
                displayMetrics(statusData);
                
                // Load trains
                const trainsResponse = await fetch('/api/trains');
                const trainsData = await trainsResponse.json();
                displayTrains(trainsData);
                
                // Load schedules
                const schedulesResponse = await fetch('/api/schedules');
                const schedulesData = await schedulesResponse.json();
                displaySchedules(schedulesData);
                
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }
        
        function displayMetrics(data) {
            const metricsDiv = document.getElementById('metrics');
            metricsDiv.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${data.active_trains}</div>
                    <div class="metric-label">Active Trains</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.on_time_percentage}%</div>
                    <div class="metric-label">On-Time Performance</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.total_tracks}</div>
                    <div class="metric-label">Railway Tracks</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${data.optimization_runs}</div>
                    <div class="metric-label">AI Optimizations</div>
                </div>
            `;
        }
        
        function displayTrains(trains) {
            const tbody = document.getElementById('trains-data');
            tbody.innerHTML = trains.map(train => `
                <tr>
                    <td><strong>${train.number}</strong></td>
                    <td>${train.name}</td>
                    <td><span class="status-badge">${train.train_type}</span></td>
                    <td><span class="status-badge priority-${train.priority}">${train.priority}</span></td>
                    <td>${train.max_speed_kmh} km/h</td>
                    <td><span class="status-badge status-${train.is_active ? 'running' : 'scheduled'}">${train.is_active ? 'Active' : 'Inactive'}</span></td>
                </tr>
            `).join('');
        }
        
        function displaySchedules(schedules) {
            const tbody = document.getElementById('schedules-data');
            tbody.innerHTML = schedules.map(schedule => `
                <tr>
                    <td>Train ${schedule.train_id}</td>
                    <td>Track ${schedule.track_id}</td>
                    <td>${new Date(schedule.scheduled_departure).toLocaleString()}</td>
                    <td>${new Date(schedule.scheduled_arrival).toLocaleString()}</td>
                    <td><span class="status-badge status-${schedule.status}">${schedule.status}</span></td>
                    <td>${schedule.delay_minutes > 0 ? '+' : ''}${schedule.delay_minutes} min</td>
                </tr>
            `).join('');
        }
        
        async function runOptimization() {
            try {
                const response = await fetch('/api/optimization/run');
                const result = await response.json();
                alert(`AI Optimization Complete!\\n\\nImprovement: ${result.improvement}\\nSchedules optimized: ${result.schedules_optimized}\\nConflicts resolved: ${result.conflicts_resolved}`);
                loadData(); // Refresh data
            } catch (error) {
                console.error('Optimization error:', error);
                alert('Optimization completed with mock results for demo purposes.');
            }
        }
        
        // Load data on page load
        loadData();
        
        // Auto-refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def get_trains(self):
        """Get all trains"""
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT * FROM trains WHERE is_active = 1')
        trains = []
        for row in cursor.fetchall():
            trains.append({
                'id': row[0],
                'number': row[1],
                'name': row[2],
                'train_type': row[3],
                'priority': row[4],
                'max_speed_kmh': row[5],
                'is_active': bool(row[6])
            })
        
        self.send_json_response(trains)
    
    def get_tracks(self):
        """Get all tracks"""
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT * FROM tracks')
        tracks = []
        for row in cursor.fetchall():
            tracks.append({
                'id': row[0],
                'name': row[1],
                'start_station': row[2],
                'end_station': row[3],
                'length_km': row[4],
                'max_speed_kmh': row[5],
                'capacity': row[6]
            })
        
        self.send_json_response(tracks)
    
    def get_schedules(self):
        """Get all schedules"""
        cursor = self.db_conn.cursor()
        cursor.execute('SELECT * FROM schedules ORDER BY scheduled_departure')
        schedules = []
        for row in cursor.fetchall():
            schedules.append({
                'id': row[0],
                'train_id': row[1],
                'track_id': row[2],
                'scheduled_departure': row[3],
                'scheduled_arrival': row[4],
                'status': row[5],
                'delay_minutes': row[6]
            })
        
        self.send_json_response(schedules)
    
    def get_system_status(self):
        """Get system status and metrics"""
        cursor = self.db_conn.cursor()
        
        # Count active trains
        cursor.execute('SELECT COUNT(*) FROM trains WHERE is_active = 1')
        active_trains = cursor.fetchone()[0]
        
        # Count tracks
        cursor.execute('SELECT COUNT(*) FROM tracks')
        total_tracks = cursor.fetchone()[0]
        
        # Calculate on-time performance (mock)
        on_time_percentage = random.randint(85, 95)
        
        status = {
            'active_trains': active_trains,
            'total_tracks': total_tracks,
            'on_time_percentage': on_time_percentage,
            'optimization_runs': random.randint(10, 50),
            'system_health': 'operational',
            'last_updated': datetime.now().isoformat()
        }
        
        self.send_json_response(status)
    
    def get_analytics(self):
        """Get performance analytics"""
        analytics = {
            'total_trips': random.randint(100, 500),
            'on_time_percentage': random.randint(85, 95),
            'average_delay_minutes': round(random.uniform(2, 8), 1),
            'worst_delay_minutes': random.randint(15, 45),
            'conflicts_detected': random.randint(5, 15),
            'conflicts_resolved': random.randint(4, 14)
        }
        
        self.send_json_response(analytics)
    
    def run_optimization(self):
        """Run AI optimization (simulation)"""
        # Simulate optimization process
        time.sleep(0.5)  # Simulate computation time
        
        result = {
            'status': 'completed',
            'improvement': f"{random.randint(5, 15)}% efficiency gain",
            'schedules_optimized': random.randint(8, 20),
            'conflicts_resolved': random.randint(2, 8),
            'computation_time_ms': random.randint(500, 2000),
            'algorithm_used': 'MILP with Constraint Satisfaction',
            'timestamp': datetime.now().isoformat()
        }
        
        self.send_json_response(result)
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        """Override to reduce log verbosity"""
        return

def create_handler_with_db(db_conn):
    """Create handler class with database connection"""
    def handler(*args, **kwargs):
        return TrainControlHandler(*args, db_conn=db_conn, **kwargs)
    return handler

def main():
    """Main function to start the demo server"""
    print("🚆 AI-Powered Train Traffic Control System - Demo Server")
    print("=" * 60)
    
    # Initialize database
    db_conn = init_database()
    print("✅ Database initialized with sample data")
    
    # Create server
    PORT = 8000
    handler_class = create_handler_with_db(db_conn)
    
    try:
        with socketserver.TCPServer(("", PORT), handler_class) as httpd:
            print(f"🌐 Server running at: http://localhost:{PORT}")
            print("📊 Dashboard: http://localhost:{PORT}")
            print("🔌 API endpoints available at /api/*")
            print("=" * 60)
            print("Press Ctrl+C to stop the server")
            
            httpd.serve_forever()
    
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
        db_conn.close()
        print("✅ Server stopped successfully")

if __name__ == "__main__":
    main()