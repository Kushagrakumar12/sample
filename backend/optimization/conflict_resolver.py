"""
Conflict detection and resolution system
Uses constraint satisfaction and graph algorithms
"""

import networkx as nx
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from ..models.database import Train, Track, Schedule, TrainMovement, TrainStatus, Priority

class ConflictResolver:
    """Conflict detection and resolution for train operations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def detect_conflicts(self, time_horizon_hours: int = 4) -> List[Dict[str, Any]]:
        """
        Detect potential conflicts between trains
        
        Args:
            time_horizon_hours: Time window to analyze
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        current_time = datetime.now()
        end_time = current_time + timedelta(hours=time_horizon_hours)
        
        # Get active schedules in time window
        active_schedules = (
            self.db.query(Schedule)
            .filter(Schedule.status.in_([TrainStatus.SCHEDULED, TrainStatus.RUNNING]))
            .filter(Schedule.scheduled_departure <= end_time)
            .filter(Schedule.scheduled_arrival >= current_time)
            .all()
        )
        
        # Group schedules by track
        track_schedules = defaultdict(list)
        for schedule in active_schedules:
            track_schedules[schedule.track_id].append(schedule)
        
        # Check for conflicts on each track
        for track_id, schedules in track_schedules.items():
            track = self.db.query(Track).filter(Track.id == track_id).first()
            if not track:
                continue
                
            # Sort schedules by departure time
            schedules.sort(key=lambda s: s.scheduled_departure)
            
            # Check for overlapping schedules
            for i in range(len(schedules)):
                for j in range(i + 1, len(schedules)):
                    conflict = self._check_schedule_conflict(schedules[i], schedules[j], track)
                    if conflict:
                        conflicts.append(conflict)
        
        # Check for station platform conflicts
        station_conflicts = self._detect_station_conflicts(active_schedules)
        conflicts.extend(station_conflicts)
        
        # Check for signal conflicts
        signal_conflicts = self._detect_signal_conflicts(active_schedules)
        conflicts.extend(signal_conflicts)
        
        return conflicts
    
    def _check_schedule_conflict(self, schedule1: Schedule, schedule2: Schedule, track: Track) -> Dict[str, Any]:
        """Check if two schedules conflict on the same track"""
        # Calculate buffer times based on train types and priorities
        train1 = self.db.query(Train).filter(Train.id == schedule1.train_id).first()
        train2 = self.db.query(Train).filter(Train.id == schedule2.train_id).first()
        
        if not train1 or not train2:
            return None
        
        # Minimum separation time based on safety requirements
        min_separation = self._calculate_min_separation(train1, train2, track)
        
        # Check for time overlap with safety buffer
        s1_start = schedule1.actual_departure or schedule1.scheduled_departure
        s1_end = schedule1.actual_arrival or schedule1.scheduled_arrival
        s2_start = schedule2.actual_departure or schedule2.scheduled_departure
        s2_end = schedule2.actual_arrival or schedule2.scheduled_arrival
        
        # Add safety buffers
        s1_start_buffered = s1_start - min_separation
        s1_end_buffered = s1_end + min_separation
        s2_start_buffered = s2_start - min_separation
        s2_end_buffered = s2_end + min_separation
        
        # Check for overlap
        if (s1_start_buffered <= s2_end_buffered and s1_end_buffered >= s2_start_buffered):
            severity = self._calculate_conflict_severity(train1, train2, s1_start, s2_start)
            
            return {
                "train1_id": train1.id,
                "train1_number": train1.number,
                "train2_id": train2.id,
                "train2_number": train2.number,
                "track_id": track.id,
                "track_name": track.name,
                "conflict_time": min(s1_start, s2_start),
                "severity": severity,
                "time_overlap_minutes": self._calculate_overlap_minutes(s1_start, s1_end, s2_start, s2_end),
                "resolution": self._suggest_resolution(schedule1, schedule2, train1, train2)
            }
        
        return None
    
    def _detect_station_conflicts(self, schedules: List[Schedule]) -> List[Dict[str, Any]]:
        """Detect conflicts at station platforms"""
        conflicts = []
        
        # Group by stations (simplified - using track start/end stations)
        station_arrivals = defaultdict(list)
        
        for schedule in schedules:
            track = self.db.query(Track).filter(Track.id == schedule.track_id).first()
            if track:
                arrival_time = schedule.actual_arrival or schedule.scheduled_arrival
                station_arrivals[track.end_station].append({
                    "schedule": schedule,
                    "time": arrival_time,
                    "track": track
                })
        
        # Check for platform capacity conflicts
        for station, arrivals in station_arrivals.items():
            arrivals.sort(key=lambda x: x["time"])
            
            # Assume maximum 3 platforms per station (simplified)
            platform_capacity = 3
            platform_occupancy = []
            
            for arrival in arrivals:
                # Remove trains that have departed
                current_time = arrival["time"]
                platform_occupancy = [
                    p for p in platform_occupancy 
                    if p["departure_time"] > current_time
                ]
                
                if len(platform_occupancy) >= platform_capacity:
                    conflicts.append({
                        "type": "station_capacity",
                        "station": station,
                        "conflict_time": current_time,
                        "severity": "medium",
                        "train_id": arrival["schedule"].train_id,
                        "message": f"Platform capacity exceeded at {station}",
                        "resolution": "Delay arrival or use alternate platform"
                    })
                
                # Add current train to platform occupancy
                # Assume 15-minute platform occupation time
                departure_time = current_time + timedelta(minutes=15)
                platform_occupancy.append({
                    "train_id": arrival["schedule"].train_id,
                    "departure_time": departure_time
                })
        
        return conflicts
    
    def _detect_signal_conflicts(self, schedules: List[Schedule]) -> List[Dict[str, Any]]:
        """Detect signal-related conflicts"""
        conflicts = []
        
        # This is a simplified implementation
        # In reality, would need detailed signal placement and control logic
        
        for schedule in schedules:
            train = self.db.query(Train).filter(Train.id == schedule.train_id).first()
            if not train:
                continue
            
            # Check if train is approaching a red signal (simulated)
            # In practice, this would query actual signal states
            
            # Simulate signal conflicts for high-priority trains
            if train.priority in [Priority.HIGH, Priority.CRITICAL]:
                departure_time = schedule.actual_departure or schedule.scheduled_departure
                if departure_time <= datetime.now() + timedelta(minutes=30):
                    conflicts.append({
                        "type": "signal_priority",
                        "train_id": train.id,
                        "track_id": schedule.track_id,
                        "conflict_time": departure_time,
                        "severity": "high",
                        "message": f"High-priority train {train.number} requires signal priority",
                        "resolution": "Clear signals and hold lower-priority trains"
                    })
        
        return conflicts
    
    def resolve_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve a specific conflict with automated suggestions
        
        Args:
            conflict: Conflict information dictionary
            
        Returns:
            Resolution plan
        """
        resolution_type = conflict.get("type", "schedule")
        
        if resolution_type == "schedule":
            return self._resolve_schedule_conflict(conflict)
        elif resolution_type == "station_capacity":
            return self._resolve_station_conflict(conflict)
        elif resolution_type == "signal_priority":
            return self._resolve_signal_conflict(conflict)
        else:
            return {"resolution": "manual_intervention", "message": "Requires manual resolution"}
    
    def _resolve_schedule_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve schedule-based conflicts"""
        train1_id = conflict["train1_id"]
        train2_id = conflict["train2_id"]
        
        train1 = self.db.query(Train).filter(Train.id == train1_id).first()
        train2 = self.db.query(Train).filter(Train.id == train2_id).first()
        
        if not train1 or not train2:
            return {"resolution": "error", "message": "Trains not found"}
        
        # Priority-based resolution
        if train1.priority.value > train2.priority.value:
            # Give priority to train1, delay train2
            delay_minutes = conflict.get("time_overlap_minutes", 15) + 10
            return {
                "resolution": "delay_lower_priority",
                "delay_train_id": train2_id,
                "delay_minutes": delay_minutes,
                "priority_train_id": train1_id,
                "message": f"Delay train {train2.number} by {delay_minutes} minutes"
            }
        elif train2.priority.value > train1.priority.value:
            delay_minutes = conflict.get("time_overlap_minutes", 15) + 10
            return {
                "resolution": "delay_lower_priority",
                "delay_train_id": train1_id,
                "delay_minutes": delay_minutes,
                "priority_train_id": train2_id,
                "message": f"Delay train {train1.number} by {delay_minutes} minutes"
            }
        else:
            # Same priority - try alternate routing
            alternate_tracks = self._find_alternate_tracks(conflict["track_id"])
            if alternate_tracks:
                return {
                    "resolution": "alternate_route",
                    "train_id": train2_id,  # Reroute second train
                    "alternate_tracks": alternate_tracks,
                    "message": f"Reroute train {train2.number} to alternate track"
                }
            else:
                # Last resort - delay the later train
                delay_minutes = 20
                later_train_id = train2_id if conflict["conflict_time"] else train1_id
                return {
                    "resolution": "delay_later_train",
                    "delay_train_id": later_train_id,
                    "delay_minutes": delay_minutes,
                    "message": f"Delay later train by {delay_minutes} minutes"
                }
    
    def _resolve_station_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve station capacity conflicts"""
        return {
            "resolution": "platform_management",
            "train_id": conflict["train_id"],
            "delay_minutes": 10,
            "message": "Hold train at previous station until platform available"
        }
    
    def _resolve_signal_conflict(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve signal priority conflicts"""
        return {
            "resolution": "signal_priority",
            "train_id": conflict["train_id"],
            "message": "Grant signal priority and clear path"
        }
    
    def _calculate_min_separation(self, train1: Train, train2: Train, track: Track) -> timedelta:
        """Calculate minimum separation time between trains"""
        # Base separation time
        base_minutes = 10  # 10 minutes minimum
        
        # Adjust based on train types
        if train1.train_type == "freight" or train2.train_type == "freight":
            base_minutes += 5  # Extra time for freight trains
        
        # Adjust based on track characteristics
        if track.gradient > 2.0:  # Steep gradient
            base_minutes += 5
        
        return timedelta(minutes=base_minutes)
    
    def _calculate_conflict_severity(self, train1: Train, train2: Train, time1: datetime, time2: datetime) -> str:
        """Calculate conflict severity based on train priorities and timing"""
        priority_sum = train1.priority.value + train2.priority.value
        time_diff = abs((time1 - time2).total_seconds() / 60)  # Minutes
        
        if priority_sum >= 6 or time_diff < 5:  # High priority trains or very close timing
            return "critical"
        elif priority_sum >= 4 or time_diff < 15:
            return "high"
        elif time_diff < 30:
            return "medium"
        else:
            return "low"
    
    def _calculate_overlap_minutes(self, s1_start: datetime, s1_end: datetime, 
                                 s2_start: datetime, s2_end: datetime) -> int:
        """Calculate time overlap between two schedules in minutes"""
        overlap_start = max(s1_start, s2_start)
        overlap_end = min(s1_end, s2_end)
        
        if overlap_end > overlap_start:
            return int((overlap_end - overlap_start).total_seconds() / 60)
        return 0
    
    def _suggest_resolution(self, schedule1: Schedule, schedule2: Schedule, 
                          train1: Train, train2: Train) -> str:
        """Suggest resolution strategy for conflict"""
        if train1.priority.value > train2.priority.value:
            return f"Give priority to {train1.number}, delay {train2.number}"
        elif train2.priority.value > train1.priority.value:
            return f"Give priority to {train2.number}, delay {train1.number}"
        else:
            return "Consider alternate routing or time adjustment"
    
    def _find_alternate_tracks(self, current_track_id: int) -> List[Dict[str, Any]]:
        """Find alternate tracks for rerouting"""
        current_track = self.db.query(Track).filter(Track.id == current_track_id).first()
        if not current_track:
            return []
        
        # Find tracks with same start/end stations (simplified)
        alternate_tracks = (
            self.db.query(Track)
            .filter(Track.id != current_track_id)
            .filter(Track.start_station == current_track.start_station)
            .filter(Track.end_station == current_track.end_station)
            .all()
        )
        
        return [
            {
                "track_id": track.id,
                "track_name": track.name,
                "additional_distance_km": abs(track.length_km - current_track.length_km),
                "max_speed_difference": track.max_speed_kmh - current_track.max_speed_kmh
            }
            for track in alternate_tracks
        ]