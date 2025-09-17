"""
Mixed Integer Linear Programming (MILP) based train scheduler
Uses PuLP library for optimization
"""

import pulp
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
import numpy as np

from ..models.database import Train, Track, Schedule, TrainStatus, TrainType, Priority

class MILPScheduler:
    """MILP-based train scheduling optimizer"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def optimize(self, time_horizon_hours: int = 24, **kwargs) -> Dict[str, Any]:
        """
        Optimize train schedules using MILP
        
        Args:
            time_horizon_hours: Planning horizon in hours
            **kwargs: Additional optimization parameters
        
        Returns:
            Dictionary with optimization results
        """
        # Get active trains and tracks
        trains = self.db.query(Train).filter(Train.is_active == True).all()
        tracks = self.db.query(Track).all()
        
        if not trains or not tracks:
            return {"error": "No active trains or tracks found"}
        
        # Create optimization problem
        prob = pulp.LpProblem("Train_Scheduling", pulp.LpMinimize)
        
        # Time discretization (15-minute intervals)
        time_slots = int(time_horizon_hours * 4)  # 4 slots per hour
        
        # Decision variables
        # x[i,j,t] = 1 if train i is assigned to track j starting at time t
        x = {}
        for train in trains:
            for track in tracks:
                for t in range(time_slots):
                    x[(train.id, track.id, t)] = pulp.LpVariable(
                        f"x_{train.id}_{track.id}_{t}",
                        cat='Binary'
                    )
        
        # Delay variables for soft constraints
        delay = {}
        for train in trains:
            delay[train.id] = pulp.LpVariable(
                f"delay_{train.id}",
                lowBound=0,
                cat='Continuous'
            )
        
        # Objective function: minimize total weighted delay
        priority_weights = {
            Priority.LOW: 1,
            Priority.MEDIUM: 2, 
            Priority.HIGH: 5,
            Priority.CRITICAL: 10
        }
        
        objective_terms = []
        for train in trains:
            weight = priority_weights.get(train.priority, 2)
            # Add penalty for passenger trains
            if train.train_type == TrainType.PASSENGER:
                weight *= 2
            objective_terms.append(weight * delay[train.id])
        
        prob += pulp.lpSum(objective_terms)
        
        # Constraints
        
        # 1. Each train must be assigned to exactly one track-time combination
        for train in trains:
            prob += pulp.lpSum([
                x[(train.id, track.id, t)] 
                for track in tracks 
                for t in range(time_slots)
            ]) == 1
        
        # 2. Track capacity constraints
        for track in tracks:
            for t in range(time_slots):
                # Estimate journey duration (simplified)
                prob += pulp.lpSum([
                    x[(train.id, track.id, s)]
                    for train in trains
                    for s in range(max(0, t-8), min(time_slots, t+8))  # 2-hour window
                ]) <= track.capacity
        
        # 3. Safety constraints - minimum separation between trains
        min_separation = 2  # 2 time slots (30 minutes)
        for track in tracks:
            for t in range(time_slots - min_separation):
                prob += pulp.lpSum([
                    x[(train.id, track.id, s)]
                    for train in trains
                    for s in range(t, t + min_separation)
                ]) <= 1
        
        # 4. Delay calculation constraints
        current_time = datetime.now()
        for train in trains:
            # Get existing schedule
            existing_schedule = (
                self.db.query(Schedule)
                .filter(Schedule.train_id == train.id)
                .filter(Schedule.status.in_([TrainStatus.SCHEDULED, TrainStatus.RUNNING]))
                .first()
            )
            
            if existing_schedule:
                # Calculate preferred start time slot
                time_diff = existing_schedule.scheduled_departure - current_time
                preferred_slot = max(0, int(time_diff.total_seconds() / 900))  # 15-min slots
                
                # Add delay constraint
                for track in tracks:
                    for t in range(time_slots):
                        if t >= preferred_slot:
                            prob += delay[train.id] >= (t - preferred_slot) * 0.25 * x[(train.id, track.id, t)]
        
        # Solve the optimization problem
        solver = pulp.PULP_CBC_CMD(msg=0)  # Silent solver
        prob.solve(solver)
        
        # Extract results
        if prob.status == pulp.LpStatusOptimal:
            assignments = []
            total_delay = 0
            
            for train in trains:
                for track in tracks:
                    for t in range(time_slots):
                        if x[(train.id, track.id, t)].varValue == 1:
                            start_time = current_time + timedelta(minutes=t * 15)
                            estimated_duration = self._estimate_journey_time(train, track)
                            end_time = start_time + estimated_duration
                            
                            assignments.append({
                                "train_id": train.id,
                                "train_number": train.number,
                                "track_id": track.id,
                                "track_name": track.name,
                                "scheduled_departure": start_time.isoformat(),
                                "scheduled_arrival": end_time.isoformat(),
                                "time_slot": t
                            })
                
                if train.id in delay:
                    total_delay += delay[train.id].varValue or 0
            
            return {
                "status": "optimal",
                "objective_value": pulp.value(prob.objective),
                "total_delay_hours": total_delay,
                "assignments": assignments,
                "trains_scheduled": len(assignments),
                "computation_status": "success"
            }
        
        else:
            return {
                "status": "failed",
                "computation_status": pulp.LpStatus[prob.status],
                "error": "Optimization could not find a feasible solution"
            }
    
    def _estimate_journey_time(self, train: Train, track: Track) -> timedelta:
        """Estimate journey time based on train and track characteristics"""
        # Simple estimation based on track length and train speed
        avg_speed = min(train.max_speed_kmh, track.max_speed_kmh) * 0.8  # 80% of max speed
        
        if avg_speed <= 0:
            avg_speed = 60  # Default 60 km/h
        
        journey_hours = track.length_km / avg_speed
        
        # Add buffer time for station stops, signals, etc.
        buffer_minutes = 15 + (track.length_km * 2)  # 2 minutes per km
        
        total_minutes = (journey_hours * 60) + buffer_minutes
        return timedelta(minutes=total_minutes)
    
    def update_schedules(self, optimization_result: Dict[str, Any]) -> bool:
        """
        Update database schedules based on optimization results
        
        Args:
            optimization_result: Result from optimize() method
            
        Returns:
            True if successful, False otherwise
        """
        if optimization_result.get("status") != "optimal":
            return False
        
        try:
            assignments = optimization_result.get("assignments", [])
            
            for assignment in assignments:
                # Check if schedule already exists
                existing_schedule = (
                    self.db.query(Schedule)
                    .filter(Schedule.train_id == assignment["train_id"])
                    .filter(Schedule.status == TrainStatus.SCHEDULED)
                    .first()
                )
                
                departure_time = datetime.fromisoformat(assignment["scheduled_departure"])
                arrival_time = datetime.fromisoformat(assignment["scheduled_arrival"])
                
                if existing_schedule:
                    # Update existing schedule
                    existing_schedule.track_id = assignment["track_id"]
                    existing_schedule.scheduled_departure = departure_time
                    existing_schedule.scheduled_arrival = arrival_time
                    existing_schedule.notes = "Updated by MILP optimization"
                else:
                    # Create new schedule
                    new_schedule = Schedule(
                        train_id=assignment["train_id"],
                        track_id=assignment["track_id"],
                        scheduled_departure=departure_time,
                        scheduled_arrival=arrival_time,
                        status=TrainStatus.SCHEDULED,
                        notes="Created by MILP optimization"
                    )
                    self.db.add(new_schedule)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error updating schedules: {e}")
            return False