"""
Database configuration and models for the Train Traffic Control System
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

# Database configuration
DATABASE_URL = "sqlite:///./train_control.db"  # For development, use PostgreSQL in production
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Enums for better data integrity
class TrainType(enum.Enum):
    PASSENGER = "passenger"
    FREIGHT = "freight"
    EXPRESS = "express"
    LOCAL = "local"

class TrainStatus(enum.Enum):
    SCHEDULED = "scheduled"
    RUNNING = "running"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class SignalState(enum.Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    MAINTENANCE = "maintenance"

class Priority(enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

# Database Models
class Track(Base):
    """Track/Railway line model"""
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    start_station = Column(String(100), nullable=False)
    end_station = Column(String(100), nullable=False)
    length_km = Column(Float, nullable=False)
    gradient = Column(Float, default=0.0)  # Percentage grade
    max_speed_kmh = Column(Integer, default=120)
    capacity = Column(Integer, default=1)  # Number of trains that can run simultaneously
    is_electrified = Column(Boolean, default=True)
    maintenance_schedule = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    signals = relationship("Signal", back_populates="track")
    train_movements = relationship("TrainMovement", back_populates="track")

class Signal(Base):
    """Signal control points"""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    track_id = Column(Integer, ForeignKey("tracks.id"))
    position_km = Column(Float, nullable=False)  # Position on track
    state = Column(Enum(SignalState), default=SignalState.GREEN)
    is_automated = Column(Boolean, default=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    track = relationship("Track", back_populates="signals")

class Train(Base):
    """Train model with specifications"""
    __tablename__ = "trains"
    
    id = Column(Integer, primary_key=True, index=True)
    number = Column(String(20), unique=True, index=True)
    name = Column(String(100))
    train_type = Column(Enum(TrainType), nullable=False)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    max_speed_kmh = Column(Integer, default=120)
    length_meters = Column(Float, default=200)
    capacity_passengers = Column(Integer, default=0)
    weight_tons = Column(Float, default=100)
    operator = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    schedules = relationship("Schedule", back_populates="train")
    movements = relationship("TrainMovement", back_populates="train")

class Schedule(Base):
    """Train schedule model"""
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id"))
    track_id = Column(Integer, ForeignKey("tracks.id"))
    scheduled_departure = Column(DateTime(timezone=True), nullable=False)
    scheduled_arrival = Column(DateTime(timezone=True), nullable=False)
    actual_departure = Column(DateTime(timezone=True))
    actual_arrival = Column(DateTime(timezone=True))
    status = Column(Enum(TrainStatus), default=TrainStatus.SCHEDULED)
    delay_minutes = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    train = relationship("Train", back_populates="schedules")

class TrainMovement(Base):
    """Real-time train position and movement tracking"""
    __tablename__ = "train_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id"))
    track_id = Column(Integer, ForeignKey("tracks.id"))
    current_position_km = Column(Float, nullable=False)
    current_speed_kmh = Column(Float, default=0)
    direction = Column(String(20))  # "north", "south", "east", "west"
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    train = relationship("Train", back_populates="movements")
    track = relationship("Track", back_populates="train_movements")

class Event(Base):
    """System events and alerts"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)  # "delay", "breakdown", "weather", "maintenance"
    severity = Column(String(20), default="medium")  # "low", "medium", "high", "critical"
    title = Column(String(200), nullable=False)
    description = Column(Text)
    train_id = Column(Integer, ForeignKey("trains.id"))
    track_id = Column(Integer, ForeignKey("tracks.id"))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class OptimizationResult(Base):
    """Store optimization algorithm results"""
    __tablename__ = "optimization_results"
    
    id = Column(Integer, primary_key=True, index=True)
    algorithm_used = Column(String(50), nullable=False)  # "MILP", "CSP", "Greedy"
    objective_value = Column(Float)
    computation_time_ms = Column(Integer)
    parameters = Column(Text)  # JSON string of input parameters
    result_data = Column(Text)  # JSON string of optimization results
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()