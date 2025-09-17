"""
Route optimization using graph algorithms
Uses NetworkX for shortest path and network analysis
"""

import networkx as nx
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import numpy as np

from ..models.database import Train, Track, TrainMovement, Schedule

class RouteOptimizer:
    """Route optimization using graph algorithms"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.railway_graph = None
        self._build_railway_graph()
    
    def _build_railway_graph(self):
        """Build NetworkX graph from track data"""
        self.railway_graph = nx.Graph()
        
        # Get all tracks
        tracks = self.db.query(Track).all()
        
        for track in tracks:
            # Add edge between start and end stations
            self.railway_graph.add_edge(
                track.start_station,
                track.end_station,
                track_id=track.id,
                length=track.length_km,
                max_speed=track.max_speed_kmh,
                gradient=track.gradient,
                capacity=track.capacity,
                is_electrified=track.is_electrified,
                # Calculate travel time (hours)
                travel_time=track.length_km / max(track.max_speed_kmh, 1),
                # Cost function combines time and distance
                cost=track.length_km + (track.gradient * 5)  # Penalty for steep gradients
            )
    
    def optimize_routes(self, train_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Optimize routes for specified trains
        
        Args:
            train_ids: List of train IDs to optimize
            
        Returns:
            List of optimized route recommendations
        """
        optimized_routes = []
        
        for train_id in train_ids:
            train = self.db.query(Train).filter(Train.id == train_id).first()
            if not train:
                continue
            
            # Get current/planned route
            current_schedule = (
                self.db.query(Schedule)
                .filter(Schedule.train_id == train_id)
                .filter(Schedule.status.in_(["scheduled", "running"]))
                .first()
            )
            
            if not current_schedule:
                continue
            
            current_track = self.db.query(Track).filter(Track.id == current_schedule.track_id).first()
            if not current_track:
                continue
            
            # Find optimal route
            optimal_route = self._find_optimal_route(
                train,
                current_track.start_station,
                current_track.end_station
            )
            
            if optimal_route:
                optimized_routes.append(optimal_route)
        
        return optimized_routes
    
    def _find_optimal_route(self, train: Train, origin: str, destination: str) -> Dict[str, Any]:
        """Find optimal route between origin and destination"""
        if not self.railway_graph.has_node(origin) or not self.railway_graph.has_node(destination):
            return None
        
        try:
            # Find shortest path by distance
            shortest_distance_path = nx.shortest_path(
                self.railway_graph,
                origin,
                destination,
                weight='length'
            )
            
            # Find fastest path by time
            fastest_time_path = nx.shortest_path(
                self.railway_graph,
                origin,
                destination,
                weight='travel_time'
            )
            
            # Find most cost-effective path
            cheapest_path = nx.shortest_path(
                self.railway_graph,
                origin,
                destination,
                weight='cost'
            )
            
            # Calculate metrics for each path
            paths = [
                ("shortest_distance", shortest_distance_path),
                ("fastest_time", fastest_time_path),
                ("most_cost_effective", cheapest_path)
            ]
            
            path_analysis = []
            for path_type, path in paths:
                metrics = self._calculate_path_metrics(path, train)
                path_analysis.append({
                    "type": path_type,
                    "path": path,
                    "metrics": metrics
                })
            
            # Select best path based on train characteristics
            best_path = self._select_best_path(path_analysis, train)
            
            return {
                "train_id": train.id,
                "train_number": train.number,
                "origin": origin,
                "destination": destination,
                "recommended_path": best_path["path"],
                "path_type": best_path["type"],
                "estimated_duration_hours": best_path["metrics"]["total_time"],
                "total_distance_km": best_path["metrics"]["total_distance"],
                "all_alternatives": path_analysis,
                "distance_saved_km": self._calculate_savings(path_analysis, "total_distance"),
                "time_saved_minutes": self._calculate_savings(path_analysis, "total_time") * 60
            }
        
        except nx.NetworkXNoPath:
            return {
                "train_id": train.id,
                "error": "No path found between origin and destination",
                "origin": origin,
                "destination": destination
            }
    
    def _calculate_path_metrics(self, path: List[str], train: Train) -> Dict[str, float]:
        """Calculate detailed metrics for a path"""
        if len(path) < 2:
            return {"total_distance": 0, "total_time": 0, "total_cost": 0}
        
        total_distance = 0
        total_time = 0
        total_cost = 0
        max_gradient = 0
        electrified_percentage = 0
        electrified_distance = 0
        
        for i in range(len(path) - 1):
            edge_data = self.railway_graph[path[i]][path[i + 1]]
            
            distance = edge_data.get("length", 0)
            max_speed = edge_data.get("max_speed", 60)
            gradient = edge_data.get("gradient", 0)
            is_electrified = edge_data.get("is_electrified", True)
            
            # Adjust speed based on train characteristics
            effective_speed = min(train.max_speed_kmh, max_speed)
            
            # Speed adjustment for gradient
            if gradient > 1.0:
                effective_speed *= (1 - gradient * 0.1)  # Reduce speed on steep gradients
            
            # Speed adjustment for train type
            if train.train_type.value == "freight":
                effective_speed *= 0.8  # Freight trains generally slower
            
            segment_time = distance / max(effective_speed, 1)
            
            total_distance += distance
            total_time += segment_time
            total_cost += edge_data.get("cost", distance)
            max_gradient = max(max_gradient, gradient)
            
            if is_electrified:
                electrified_distance += distance
        
        electrified_percentage = (electrified_distance / total_distance * 100) if total_distance > 0 else 0
        
        return {
            "total_distance": total_distance,
            "total_time": total_time,
            "total_cost": total_cost,
            "max_gradient": max_gradient,
            "electrified_percentage": electrified_percentage,
            "average_speed": total_distance / total_time if total_time > 0 else 0
        }
    
    def _select_best_path(self, path_analysis: List[Dict], train: Train) -> Dict[str, Any]:
        """Select best path based on train characteristics and priorities"""
        if not path_analysis:
            return None
        
        # Scoring weights based on train type and priority
        weights = {
            "passenger": {"time": 0.6, "distance": 0.2, "cost": 0.2},
            "freight": {"time": 0.3, "distance": 0.3, "cost": 0.4},
            "express": {"time": 0.8, "distance": 0.1, "cost": 0.1},
            "local": {"time": 0.4, "distance": 0.3, "cost": 0.3}
        }
        
        train_weights = weights.get(train.train_type.value, weights["passenger"])
        
        best_path = None
        best_score = float('inf')
        
        for path in path_analysis:
            metrics = path["metrics"]
            
            # Normalize metrics (simple min-max normalization)
            all_times = [p["metrics"]["total_time"] for p in path_analysis]
            all_distances = [p["metrics"]["total_distance"] for p in path_analysis]
            all_costs = [p["metrics"]["total_cost"] for p in path_analysis]
            
            norm_time = (metrics["total_time"] - min(all_times)) / (max(all_times) - min(all_times) + 0.001)
            norm_distance = (metrics["total_distance"] - min(all_distances)) / (max(all_distances) - min(all_distances) + 0.001)
            norm_cost = (metrics["total_cost"] - min(all_costs)) / (max(all_costs) - min(all_costs) + 0.001)
            
            # Calculate weighted score
            score = (
                norm_time * train_weights["time"] +
                norm_distance * train_weights["distance"] +
                norm_cost * train_weights["cost"]
            )
            
            # Bonus for electrified routes (if train needs electricity)
            if metrics["electrified_percentage"] > 90:
                score *= 0.9  # 10% bonus
            
            # Penalty for steep gradients
            if metrics["max_gradient"] > 2.0:
                score *= 1.1  # 10% penalty
            
            if score < best_score:
                best_score = score
                best_path = path
        
        return best_path
    
    def _calculate_savings(self, path_analysis: List[Dict], metric: str) -> float:
        """Calculate savings compared to worst option"""
        if len(path_analysis) < 2:
            return 0
        
        values = [p["metrics"][metric] for p in path_analysis]
        return max(values) - min(values)
    
    def get_network_analysis(self) -> Dict[str, Any]:
        """Get comprehensive railway network analysis"""
        if not self.railway_graph:
            return {"error": "No railway graph available"}
        
        # Basic network statistics
        num_stations = self.railway_graph.number_of_nodes()
        num_tracks = self.railway_graph.number_of_edges()
        
        # Connectivity analysis
        is_connected = nx.is_connected(self.railway_graph)
        num_components = nx.number_connected_components(self.railway_graph)
        
        # Centrality measures
        centrality = nx.degree_centrality(self.railway_graph)
        betweenness = nx.betweenness_centrality(self.railway_graph)
        
        # Find most important stations
        most_central_stations = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
        bottleneck_stations = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Network diameter and average path length
        try:
            diameter = nx.diameter(self.railway_graph)
            avg_path_length = nx.average_shortest_path_length(self.railway_graph)
        except:
            diameter = "N/A (disconnected)"
            avg_path_length = "N/A (disconnected)"
        
        # Identify potential bottlenecks
        bottlenecks = self._identify_bottlenecks()
        
        return {
            "network_statistics": {
                "total_stations": num_stations,
                "total_tracks": num_tracks,
                "is_fully_connected": is_connected,
                "connected_components": num_components,
                "network_diameter": diameter,
                "average_path_length": avg_path_length
            },
            "important_stations": {
                "most_central": most_central_stations,
                "bottleneck_stations": bottleneck_stations
            },
            "bottlenecks": bottlenecks,
            "optimization_opportunities": self._find_optimization_opportunities()
        }
    
    def _identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify potential network bottlenecks"""
        bottlenecks = []
        
        # Find nodes with high betweenness centrality but low degree
        betweenness = nx.betweenness_centrality(self.railway_graph)
        degree = dict(self.railway_graph.degree())
        
        for station, bet_cent in betweenness.items():
            if bet_cent > 0.1 and degree[station] <= 2:  # High betweenness, low degree
                bottlenecks.append({
                    "station": station,
                    "betweenness_centrality": bet_cent,
                    "degree": degree[station],
                    "type": "critical_junction",
                    "risk_level": "high" if bet_cent > 0.2 else "medium"
                })
        
        return bottlenecks
    
    def _find_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Find network optimization opportunities"""
        opportunities = []
        
        # Look for station pairs with high shortest path length
        try:
            all_pairs_shortest = dict(nx.all_pairs_shortest_path_length(self.railway_graph))
            
            for source in all_pairs_shortest:
                for target, length in all_pairs_shortest[source].items():
                    if length > 3:  # More than 3 hops
                        opportunities.append({
                            "type": "direct_connection",
                            "from_station": source,
                            "to_station": target,
                            "current_hops": length,
                            "potential_benefit": "high" if length > 5 else "medium",
                            "description": f"Consider direct track between {source} and {target}"
                        })
        except:
            pass  # Skip if graph is too large
        
        # Look for capacity improvements
        tracks = self.db.query(Track).all()
        for track in tracks:
            if track.capacity == 1 and track.length_km > 50:  # Long single-track sections
                opportunities.append({
                    "type": "capacity_upgrade",
                    "track_id": track.id,
                    "track_name": track.name,
                    "current_capacity": track.capacity,
                    "suggested_capacity": 2,
                    "potential_benefit": "high",
                    "description": f"Consider double-tracking {track.name}"
                })
        
        return opportunities[:10]  # Return top 10 opportunities