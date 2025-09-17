"""
Train management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..models.database import get_db, Train, TrainType, Priority, TrainStatus
from ..models.database import TrainMovement, Schedule

router = APIRouter()

# Pydantic models for API
class TrainCreate(BaseModel):
    number: str
    name: str
    train_type: TrainType
    priority: Priority = Priority.MEDIUM
    max_speed_kmh: int = 120
    length_meters: float = 200
    capacity_passengers: int = 0
    weight_tons: float = 100
    operator: str

class TrainResponse(BaseModel):
    id: int
    number: str
    name: str
    train_type: TrainType
    priority: Priority
    max_speed_kmh: int
    length_meters: float
    capacity_passengers: int
    weight_tons: float
    operator: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TrainMovementResponse(BaseModel):
    id: int
    train_id: int
    track_id: int
    current_position_km: float
    current_speed_kmh: float
    direction: str
    timestamp: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[TrainResponse])
def get_trains(
    skip: int = 0,
    limit: int = 100,
    train_type: Optional[TrainType] = None,
    db: Session = Depends(get_db)
):
    """Get all trains with optional filtering"""
    query = db.query(Train)
    
    if train_type:
        query = query.filter(Train.train_type == train_type)
    
    trains = query.offset(skip).limit(limit).all()
    return trains

@router.get("/{train_id}", response_model=TrainResponse)
def get_train(train_id: int, db: Session = Depends(get_db)):
    """Get specific train by ID"""
    train = db.query(Train).filter(Train.id == train_id).first()
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    return train

@router.post("/", response_model=TrainResponse)
def create_train(train: TrainCreate, db: Session = Depends(get_db)):
    """Create a new train"""
    # Check if train number already exists
    existing_train = db.query(Train).filter(Train.number == train.number).first()
    if existing_train:
        raise HTTPException(status_code=400, detail="Train number already exists")
    
    db_train = Train(**train.dict())
    db.add(db_train)
    db.commit()
    db.refresh(db_train)
    return db_train

@router.put("/{train_id}", response_model=TrainResponse)
def update_train(train_id: int, train_update: TrainCreate, db: Session = Depends(get_db)):
    """Update train information"""
    db_train = db.query(Train).filter(Train.id == train_id).first()
    if not db_train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    for field, value in train_update.dict().items():
        setattr(db_train, field, value)
    
    db.commit()
    db.refresh(db_train)
    return db_train

@router.delete("/{train_id}")
def delete_train(train_id: int, db: Session = Depends(get_db)):
    """Deactivate a train (soft delete)"""
    db_train = db.query(Train).filter(Train.id == train_id).first()
    if not db_train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    db_train.is_active = False
    db.commit()
    return {"message": "Train deactivated successfully"}

@router.get("/{train_id}/position", response_model=List[TrainMovementResponse])
def get_train_positions(
    train_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent positions for a specific train"""
    train = db.query(Train).filter(Train.id == train_id).first()
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    movements = (
        db.query(TrainMovement)
        .filter(TrainMovement.train_id == train_id)
        .order_by(TrainMovement.timestamp.desc())
        .limit(limit)
        .all()
    )
    
    return movements

@router.get("/{train_id}/status")
def get_train_status(train_id: int, db: Session = Depends(get_db)):
    """Get comprehensive train status including current position and schedule"""
    train = db.query(Train).filter(Train.id == train_id).first()
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    # Get latest position
    latest_movement = (
        db.query(TrainMovement)
        .filter(TrainMovement.train_id == train_id)
        .order_by(TrainMovement.timestamp.desc())
        .first()
    )
    
    # Get current schedule
    current_schedule = (
        db.query(Schedule)
        .filter(Schedule.train_id == train_id)
        .filter(Schedule.status.in_([TrainStatus.SCHEDULED, TrainStatus.RUNNING]))
        .order_by(Schedule.scheduled_departure.desc())
        .first()
    )
    
    return {
        "train": train,
        "current_position": latest_movement,
        "current_schedule": current_schedule,
        "is_running": latest_movement is not None and latest_movement.current_speed_kmh > 0
    }