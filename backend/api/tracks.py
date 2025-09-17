"""
Track and railway infrastructure API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.database import get_db, Track, Signal, SignalState

router = APIRouter()

# Pydantic models
class TrackCreate(BaseModel):
    name: str
    start_station: str
    end_station: str
    length_km: float
    gradient: float = 0.0
    max_speed_kmh: int = 120
    capacity: int = 1
    is_electrified: bool = True
    maintenance_schedule: Optional[str] = None

class TrackResponse(BaseModel):
    id: int
    name: str
    start_station: str
    end_station: str
    length_km: float
    gradient: float
    max_speed_kmh: int
    capacity: int
    is_electrified: bool
    maintenance_schedule: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class SignalCreate(BaseModel):
    name: str
    track_id: int
    position_km: float
    state: SignalState = SignalState.GREEN
    is_automated: bool = True

class SignalResponse(BaseModel):
    id: int
    name: str
    track_id: int
    position_km: float
    state: SignalState
    is_automated: bool
    last_updated: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[TrackResponse])
def get_tracks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all tracks"""
    tracks = db.query(Track).offset(skip).limit(limit).all()
    return tracks

@router.get("/{track_id}", response_model=TrackResponse)
def get_track(track_id: int, db: Session = Depends(get_db)):
    """Get specific track by ID"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track

@router.post("/", response_model=TrackResponse)
def create_track(track: TrackCreate, db: Session = Depends(get_db)):
    """Create a new track"""
    # Check if track name already exists
    existing_track = db.query(Track).filter(Track.name == track.name).first()
    if existing_track:
        raise HTTPException(status_code=400, detail="Track name already exists")
    
    db_track = Track(**track.dict())
    db.add(db_track)
    db.commit()
    db.refresh(db_track)
    return db_track

@router.get("/{track_id}/signals", response_model=List[SignalResponse])
def get_track_signals(track_id: int, db: Session = Depends(get_db)):
    """Get all signals for a specific track"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    signals = db.query(Signal).filter(Signal.track_id == track_id).all()
    return signals

@router.post("/signals", response_model=SignalResponse)
def create_signal(signal: SignalCreate, db: Session = Depends(get_db)):
    """Create a new signal"""
    # Verify track exists
    track = db.query(Track).filter(Track.id == signal.track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Check if signal name already exists
    existing_signal = db.query(Signal).filter(Signal.name == signal.name).first()
    if existing_signal:
        raise HTTPException(status_code=400, detail="Signal name already exists")
    
    db_signal = Signal(**signal.dict())
    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)
    return db_signal

@router.put("/signals/{signal_id}/state")
def update_signal_state(
    signal_id: int,
    new_state: SignalState,
    db: Session = Depends(get_db)
):
    """Update signal state"""
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    signal.state = new_state
    signal.last_updated = datetime.utcnow()
    db.commit()
    
    return {"message": f"Signal {signal.name} updated to {new_state.value}"}

@router.get("/{track_id}/capacity")
def get_track_capacity(track_id: int, db: Session = Depends(get_db)):
    """Get current track capacity utilization"""
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Count active trains on this track (simplified for demo)
    from ..models.database import TrainMovement
    active_trains = (
        db.query(TrainMovement)
        .filter(TrainMovement.track_id == track_id)
        .filter(TrainMovement.current_speed_kmh > 0)
        .count()
    )
    
    utilization = (active_trains / track.capacity) * 100 if track.capacity > 0 else 0
    
    return {
        "track_id": track_id,
        "track_name": track.name,
        "capacity": track.capacity,
        "active_trains": active_trains,
        "utilization_percent": round(utilization, 2),
        "available_capacity": max(0, track.capacity - active_trains)
    }