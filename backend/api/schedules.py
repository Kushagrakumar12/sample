"""
Schedule management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..models.database import get_db, Schedule, Train, Track, TrainStatus

router = APIRouter()

# Pydantic models
class ScheduleCreate(BaseModel):
    train_id: int
    track_id: int
    scheduled_departure: datetime
    scheduled_arrival: datetime
    notes: Optional[str] = None

class ScheduleResponse(BaseModel):
    id: int
    train_id: int
    track_id: int
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: Optional[datetime]
    actual_arrival: Optional[datetime]
    status: TrainStatus
    delay_minutes: int
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ScheduleResponse])
def get_schedules(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TrainStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get all schedules with optional filtering"""
    query = db.query(Schedule)
    
    if status:
        query = query.filter(Schedule.status == status)
    
    if date_from:
        query = query.filter(Schedule.scheduled_departure >= date_from)
    
    if date_to:
        query = query.filter(Schedule.scheduled_departure <= date_to)
    
    schedules = query.offset(skip).limit(limit).all()
    return schedules

@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Get specific schedule by ID"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

@router.post("/", response_model=ScheduleResponse)
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a new schedule"""
    # Verify train exists
    train = db.query(Train).filter(Train.id == schedule.train_id).first()
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    
    # Verify track exists
    track = db.query(Track).filter(Track.id == schedule.track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Basic validation
    if schedule.scheduled_arrival <= schedule.scheduled_departure:
        raise HTTPException(status_code=400, detail="Arrival time must be after departure time")
    
    db_schedule = Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.put("/{schedule_id}/departure")
def record_departure(schedule_id: int, departure_time: datetime, db: Session = Depends(get_db)):
    """Record actual departure time"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.actual_departure = departure_time
    schedule.status = TrainStatus.RUNNING
    
    # Calculate delay
    delay = departure_time - schedule.scheduled_departure
    schedule.delay_minutes = int(delay.total_seconds() / 60)
    
    db.commit()
    return {"message": "Departure recorded", "delay_minutes": schedule.delay_minutes}

@router.put("/{schedule_id}/arrival")
def record_arrival(schedule_id: int, arrival_time: datetime, db: Session = Depends(get_db)):
    """Record actual arrival time"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule.actual_arrival = arrival_time
    schedule.status = TrainStatus.COMPLETED
    
    # Update delay based on arrival time
    delay = arrival_time - schedule.scheduled_arrival
    schedule.delay_minutes = int(delay.total_seconds() / 60)
    
    db.commit()
    return {"message": "Arrival recorded", "delay_minutes": schedule.delay_minutes}

@router.get("/analytics/performance")
def get_performance_analytics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get performance analytics for schedules"""
    query = db.query(Schedule).filter(Schedule.status == TrainStatus.COMPLETED)
    
    if not date_from:
        date_from = datetime.now() - timedelta(days=30)
    if not date_to:
        date_to = datetime.now()
    
    query = query.filter(Schedule.scheduled_departure >= date_from)
    query = query.filter(Schedule.scheduled_departure <= date_to)
    
    completed_schedules = query.all()
    
    if not completed_schedules:
        return {
            "total_trips": 0,
            "on_time_percentage": 0,
            "average_delay_minutes": 0,
            "worst_delay_minutes": 0
        }
    
    total_trips = len(completed_schedules)
    on_time_trips = len([s for s in completed_schedules if s.delay_minutes <= 5])  # Within 5 minutes
    delays = [s.delay_minutes for s in completed_schedules]
    
    return {
        "total_trips": total_trips,
        "on_time_percentage": round((on_time_trips / total_trips) * 100, 2),
        "average_delay_minutes": round(sum(delays) / len(delays), 2),
        "worst_delay_minutes": max(delays) if delays else 0,
        "date_range": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        }
    }