"""
Optimization and AI decision-support API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json

from ..models.database import get_db, Train, Track, Schedule, OptimizationResult
from ..optimization.milp_scheduler import MILPScheduler
from ..optimization.conflict_resolver import ConflictResolver
from ..optimization.route_optimizer import RouteOptimizer

router = APIRouter()

# Pydantic models
class OptimizationRequest(BaseModel):
    algorithm: str  # "milp", "conflict_resolution", "route_optimization"
    parameters: Dict[str, Any]
    time_horizon_hours: int = 24

class OptimizationResponse(BaseModel):
    id: int
    algorithm_used: str
    objective_value: Optional[float]
    computation_time_ms: int
    parameters: str
    result_data: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConflictAlert(BaseModel):
    train1_id: int
    train2_id: int
    track_id: int
    conflict_time: datetime
    severity: str
    resolution_suggestion: str

@router.post("/schedule", response_model=OptimizationResponse)
def optimize_schedule(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Run MILP-based schedule optimization"""
    if request.algorithm != "milp":
        raise HTTPException(status_code=400, detail="Algorithm must be 'milp' for this endpoint")
    
    # Initialize MILP scheduler
    scheduler = MILPScheduler(db)
    
    try:
        # Run optimization
        start_time = datetime.now()
        result = scheduler.optimize(
            time_horizon_hours=request.time_horizon_hours,
            **request.parameters
        )
        end_time = datetime.now()
        
        computation_time = int((end_time - start_time).total_seconds() * 1000)
        
        # Store result
        db_result = OptimizationResult(
            algorithm_used="MILP",
            objective_value=result.get("objective_value"),
            computation_time_ms=computation_time,
            parameters=json.dumps(request.parameters),
            result_data=json.dumps(result)
        )
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        
        return db_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.post("/conflicts/detect")
def detect_conflicts(
    time_horizon_hours: int = 4,
    db: Session = Depends(get_db)
) -> List[ConflictAlert]:
    """Detect potential train conflicts"""
    conflict_resolver = ConflictResolver(db)
    
    try:
        conflicts = conflict_resolver.detect_conflicts(time_horizon_hours)
        
        alerts = []
        for conflict in conflicts:
            alerts.append(ConflictAlert(
                train1_id=conflict["train1_id"],
                train2_id=conflict["train2_id"],
                track_id=conflict["track_id"],
                conflict_time=conflict["conflict_time"],
                severity=conflict["severity"],
                resolution_suggestion=conflict["resolution"]
            ))
        
        return alerts
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conflict detection failed: {str(e)}")

@router.post("/conflicts/resolve")
def resolve_conflicts(
    conflicts: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """Resolve detected conflicts with automated suggestions"""
    conflict_resolver = ConflictResolver(db)
    
    try:
        resolutions = []
        for conflict in conflicts:
            resolution = conflict_resolver.resolve_conflict(conflict)
            resolutions.append(resolution)
        
        return {
            "resolved_conflicts": len(resolutions),
            "resolutions": resolutions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conflict resolution failed: {str(e)}")

@router.post("/routes/optimize")
def optimize_routes(
    train_ids: List[int],
    db: Session = Depends(get_db)
):
    """Optimize routes for specified trains"""
    route_optimizer = RouteOptimizer(db)
    
    try:
        # Verify all trains exist
        trains = db.query(Train).filter(Train.id.in_(train_ids)).all()
        if len(trains) != len(train_ids):
            raise HTTPException(status_code=404, detail="One or more trains not found")
        
        optimized_routes = route_optimizer.optimize_routes(train_ids)
        
        return {
            "optimized_trains": len(train_ids),
            "routes": optimized_routes,
            "total_distance_saved_km": sum(r.get("distance_saved_km", 0) for r in optimized_routes),
            "total_time_saved_minutes": sum(r.get("time_saved_minutes", 0) for r in optimized_routes)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route optimization failed: {str(e)}")

@router.get("/recommendations")
def get_optimization_recommendations(
    train_id: Optional[int] = None,
    track_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get AI-powered recommendations for train operations"""
    recommendations = []
    
    # Get current system state
    current_time = datetime.now()
    
    # Check for delayed trains
    delayed_schedules = (
        db.query(Schedule)
        .filter(Schedule.status.in_(["scheduled", "running"]))
        .filter(Schedule.delay_minutes > 5)
        .all()
    )
    
    for schedule in delayed_schedules:
        recommendations.append({
            "type": "delay_management",
            "priority": "high" if schedule.delay_minutes > 15 else "medium",
            "train_id": schedule.train_id,
            "track_id": schedule.track_id,
            "message": f"Train {schedule.train_id} delayed by {schedule.delay_minutes} minutes",
            "suggested_action": "Consider rerouting or adjusting downstream schedules",
            "confidence": 0.85
        })
    
    # Check track capacity utilization
    from sqlalchemy import func
    from ..models.database import TrainMovement
    
    track_utilization = (
        db.query(
            TrainMovement.track_id,
            func.count(TrainMovement.id).label("active_trains")
        )
        .filter(TrainMovement.current_speed_kmh > 0)
        .group_by(TrainMovement.track_id)
        .all()
    )
    
    for track_id, active_trains in track_utilization:
        track = db.query(Track).filter(Track.id == track_id).first()
        if track and active_trains >= track.capacity * 0.8:  # 80% utilization threshold
            recommendations.append({
                "type": "capacity_management",
                "priority": "medium",
                "track_id": track_id,
                "message": f"Track {track.name} at {(active_trains/track.capacity)*100:.1f}% capacity",
                "suggested_action": "Consider load balancing to alternate routes",
                "confidence": 0.75
            })
    
    return {
        "timestamp": current_time.isoformat(),
        "total_recommendations": len(recommendations),
        "recommendations": recommendations
    }

@router.get("/results", response_model=List[OptimizationResponse])
def get_optimization_results(
    skip: int = 0,
    limit: int = 50,
    algorithm: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get historical optimization results"""
    query = db.query(OptimizationResult)
    
    if algorithm:
        query = query.filter(OptimizationResult.algorithm_used == algorithm.upper())
    
    results = query.order_by(OptimizationResult.created_at.desc()).offset(skip).limit(limit).all()
    return results