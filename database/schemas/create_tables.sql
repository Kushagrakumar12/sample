-- AI-Powered Train Traffic Control System Database Schema
-- PostgreSQL version

-- Create database
-- CREATE DATABASE train_control_system;

-- Use the database
-- \c train_control_system;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create ENUM types
CREATE TYPE train_type_enum AS ENUM ('passenger', 'freight', 'express', 'local');
CREATE TYPE train_status_enum AS ENUM ('scheduled', 'running', 'delayed', 'cancelled', 'completed');
CREATE TYPE signal_state_enum AS ENUM ('green', 'yellow', 'red', 'maintenance');
CREATE TYPE priority_enum AS ENUM ('low', 'medium', 'high', 'critical');

-- Create tables

-- Tracks table
CREATE TABLE tracks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    start_station VARCHAR(100) NOT NULL,
    end_station VARCHAR(100) NOT NULL,
    length_km DECIMAL(8,2) NOT NULL CHECK (length_km > 0),
    gradient DECIMAL(5,2) DEFAULT 0.0,
    max_speed_kmh INTEGER DEFAULT 120 CHECK (max_speed_kmh > 0),
    capacity INTEGER DEFAULT 1 CHECK (capacity > 0),
    is_electrified BOOLEAN DEFAULT true,
    maintenance_schedule VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Signals table
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    track_id INTEGER REFERENCES tracks(id) ON DELETE CASCADE,
    position_km DECIMAL(8,2) NOT NULL CHECK (position_km >= 0),
    state signal_state_enum DEFAULT 'green',
    is_automated BOOLEAN DEFAULT true,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trains table
CREATE TABLE trains (
    id SERIAL PRIMARY KEY,
    number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    train_type train_type_enum NOT NULL,
    priority priority_enum DEFAULT 'medium',
    max_speed_kmh INTEGER DEFAULT 120 CHECK (max_speed_kmh > 0),
    length_meters DECIMAL(6,2) DEFAULT 200.0 CHECK (length_meters > 0),
    capacity_passengers INTEGER DEFAULT 0 CHECK (capacity_passengers >= 0),
    weight_tons DECIMAL(8,2) DEFAULT 100.0 CHECK (weight_tons > 0),
    operator VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Schedules table
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    train_id INTEGER REFERENCES trains(id) ON DELETE CASCADE,
    track_id INTEGER REFERENCES tracks(id) ON DELETE CASCADE,
    scheduled_departure TIMESTAMP WITH TIME ZONE NOT NULL,
    scheduled_arrival TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_departure TIMESTAMP WITH TIME ZONE,
    actual_arrival TIMESTAMP WITH TIME ZONE,
    status train_status_enum DEFAULT 'scheduled',
    delay_minutes INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_schedule_times CHECK (scheduled_arrival > scheduled_departure)
);

-- Train movements table (for real-time tracking)
CREATE TABLE train_movements (
    id SERIAL PRIMARY KEY,
    train_id INTEGER REFERENCES trains(id) ON DELETE CASCADE,
    track_id INTEGER REFERENCES tracks(id) ON DELETE CASCADE,
    current_position_km DECIMAL(8,2) NOT NULL CHECK (current_position_km >= 0),
    current_speed_kmh DECIMAL(6,2) DEFAULT 0.0 CHECK (current_speed_kmh >= 0),
    direction VARCHAR(20),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Events table (for system events and alerts)
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium',
    title VARCHAR(200) NOT NULL,
    description TEXT,
    train_id INTEGER REFERENCES trains(id) ON DELETE SET NULL,
    track_id INTEGER REFERENCES tracks(id) ON DELETE SET NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Optimization results table
CREATE TABLE optimization_results (
    id SERIAL PRIMARY KEY,
    algorithm_used VARCHAR(50) NOT NULL,
    objective_value DECIMAL(12,4),
    computation_time_ms INTEGER,
    parameters TEXT, -- JSON string
    result_data TEXT, -- JSON string
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User management tables
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role VARCHAR(20) DEFAULT 'operator',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    old_values TEXT, -- JSON string
    new_values TEXT, -- JSON string
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_trains_active ON trains(is_active);
CREATE INDEX idx_trains_type ON trains(train_type);
CREATE INDEX idx_schedules_departure ON schedules(scheduled_departure);
CREATE INDEX idx_schedules_status ON schedules(status);
CREATE INDEX idx_train_movements_timestamp ON train_movements(timestamp DESC);
CREATE INDEX idx_train_movements_train_id ON train_movements(train_id);
CREATE INDEX idx_signals_track_id ON signals(track_id);
CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_events_resolved ON events(is_resolved);
CREATE INDEX idx_optimization_results_created ON optimization_results(created_at DESC);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tracks_updated_at BEFORE UPDATE ON tracks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trains_updated_at BEFORE UPDATE ON trains
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
INSERT INTO tracks (name, start_station, end_station, length_km, gradient, max_speed_kmh, capacity, is_electrified) VALUES
    ('Main Line A', 'Central Station', 'North Terminal', 85.5, 1.2, 160, 2, true),
    ('Express Route B', 'Central Station', 'East Junction', 120.0, 0.8, 200, 1, true),
    ('Freight Line C', 'Industrial Hub', 'Port Terminal', 65.3, 2.1, 80, 1, false),
    ('Local Route D', 'Suburban Center', 'Downtown', 45.2, 0.5, 100, 3, true);

INSERT INTO trains (number, name, train_type, priority, max_speed_kmh, length_meters, capacity_passengers, weight_tons, operator) VALUES
    ('T001', 'Express Morning', 'express', 'high', 180, 250.0, 400, 200.0, 'National Express'),
    ('T002', 'Local Commuter', 'passenger', 'medium', 120, 180.0, 300, 150.0, 'Metro Transit'),
    ('F001', 'Freight Heavy', 'freight', 'low', 80, 800.0, 0, 2000.0, 'Cargo Corp'),
    ('T003', 'Evening Express', 'express', 'high', 180, 250.0, 400, 200.0, 'National Express'),
    ('L001', 'Local Service', 'local', 'medium', 100, 150.0, 200, 120.0, 'Local Rail');

INSERT INTO signals (name, track_id, position_km, state, is_automated) VALUES
    ('Signal-A1', 1, 0.0, 'green', true),
    ('Signal-A2', 1, 25.5, 'green', true),
    ('Signal-A3', 1, 85.5, 'green', true),
    ('Signal-B1', 2, 0.0, 'green', true),
    ('Signal-B2', 2, 120.0, 'green', true),
    ('Signal-C1', 3, 0.0, 'yellow', true),
    ('Signal-C2', 3, 65.3, 'green', true);

-- Sample schedules (next 24 hours)
INSERT INTO schedules (train_id, track_id, scheduled_departure, scheduled_arrival, status) VALUES
    (1, 1, CURRENT_TIMESTAMP + INTERVAL '1 hour', CURRENT_TIMESTAMP + INTERVAL '2 hours', 'scheduled'),
    (2, 4, CURRENT_TIMESTAMP + INTERVAL '30 minutes', CURRENT_TIMESTAMP + INTERVAL '1 hour 15 minutes', 'scheduled'),
    (3, 3, CURRENT_TIMESTAMP + INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '4 hours', 'scheduled'),
    (4, 2, CURRENT_TIMESTAMP + INTERVAL '3 hours', CURRENT_TIMESTAMP + INTERVAL '4 hours 30 minutes', 'scheduled'),
    (5, 4, CURRENT_TIMESTAMP + INTERVAL '4 hours', CURRENT_TIMESTAMP + INTERVAL '5 hours', 'scheduled');

-- Create views for common queries
CREATE VIEW active_schedules AS
SELECT 
    s.*,
    t.number as train_number,
    t.name as train_name,
    t.train_type,
    t.priority,
    tr.name as track_name,
    tr.start_station,
    tr.end_station
FROM schedules s
JOIN trains t ON s.train_id = t.id
JOIN tracks tr ON s.track_id = tr.id
WHERE s.status IN ('scheduled', 'running')
ORDER BY s.scheduled_departure;

CREATE VIEW train_performance AS
SELECT 
    t.id,
    t.number,
    t.name,
    COUNT(s.id) as total_trips,
    AVG(s.delay_minutes) as avg_delay,
    COUNT(CASE WHEN s.delay_minutes <= 5 THEN 1 END) * 100.0 / COUNT(s.id) as on_time_percentage
FROM trains t
LEFT JOIN schedules s ON t.id = s.train_id AND s.status = 'completed'
GROUP BY t.id, t.number, t.name;

COMMENT ON DATABASE train_control_system IS 'AI-Powered Train Traffic Control System Database';
COMMENT ON TABLE tracks IS 'Railway tracks and infrastructure information';
COMMENT ON TABLE signals IS 'Signal control points along tracks';
COMMENT ON TABLE trains IS 'Train fleet information and specifications';
COMMENT ON TABLE schedules IS 'Train schedules and timetables';
COMMENT ON TABLE train_movements IS 'Real-time train position tracking';
COMMENT ON TABLE events IS 'System events, alerts, and incidents';
COMMENT ON TABLE optimization_results IS 'Results from AI optimization algorithms';