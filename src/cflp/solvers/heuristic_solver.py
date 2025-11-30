"""Heuristic solver implementation for CFLP problem.

This module provides a greedy heuristic solver for the Capacitated Facility
Location Problem. The heuristic uses a cost-benefit approach to construct
a feasible solution.
"""

import logging
import time
from typing import Any, Dict, List, Tuple

from src.cflp.config import CAFETERIA_TYPES, DISTANCE_COST_FACTOR

logger = logging.getLogger(__name__)


class HeuristicSolver:
    """Greedy heuristic solver for CFLP problem."""

    def __init__(
        self,
        demand_points: List[Dict[str, Any]],
        facility_points: List[Dict[str, Any]],
        distance_matrix: List[List[float]],
    ) -> None:
        """Initialize the heuristic solver.

        Args:
            demand_points: List of demand point dictionaries.
            facility_points: List of facility location dictionaries.
            distance_matrix: Distance matrix between demand and facility points.
        """
        self.demand_points = demand_points
        self.facility_points = facility_points
        self.distance_matrix = distance_matrix

    def solve(self) -> Dict[str, Any]:
        """Solve the CFLP problem using a greedy heuristic.

        Returns:
            Dictionary containing solution information.
        """
        logger.info("Starting heuristic solution construction")
        start_time = time.time()

        # Initialize solution
        solution = {
            "status": "heuristic",
            "objective_value": 0.0,
            "facilities_opened": [],
            "assignments": {},
            "total_fixed_cost": 0.0,
            "total_variable_cost": 0.0,
        }

        # Calculate total demand
        total_demand = sum(point["demand"] for point in self.demand_points)

        # Step 1: Calculate cost-benefit for each (facility, type) combination
        facility_options = self._calculate_facility_options()

        # Step 2: Sort options by cost-benefit (lower is better)
        facility_options.sort(key=lambda x: x["cost_benefit"])

        # Step 3: Greedy construction
        opened_facilities: Dict[int, Dict[str, Any]] = {}  # j -> {type, capacity, used_capacity}
        remaining_demand = {i: self.demand_points[i]["demand"] for i in range(len(self.demand_points))}
        # Track assignments: facility_idx -> list of (demand_idx, assigned_amount)
        facility_assignments: Dict[int, List[Tuple[int, float]]] = {}

        for option in facility_options:
            facility_idx = option["facility_idx"]
            facility_type = option["type"]
            capacity = option["capacity"]
            fixed_cost = option["fixed_cost"]

            # Skip if facility already opened
            if facility_idx in opened_facilities:
                continue

            # Calculate how much demand this facility can serve
            available_capacity = capacity

            # Try to assign demand to this facility
            assignments = self._assign_demand_to_facility_with_tracking(
                facility_idx,
                facility_type,
                available_capacity,
                remaining_demand,
            )

            if assignments:  # If any demand was assigned
                # Open facility
                opened_facilities[facility_idx] = {
                    "type": facility_type,
                    "capacity": capacity,
                    "used_capacity": 0.0,
                    "fixed_cost": fixed_cost,
                }
                solution["total_fixed_cost"] += fixed_cost
                facility_assignments[facility_idx] = []

                # Track assignments
                for demand_idx, assigned_amount in assignments:
                    opened_facilities[facility_idx]["used_capacity"] += assigned_amount
                    facility_assignments[facility_idx].append((demand_idx, assigned_amount))

        # Step 4: Ensure all demand is satisfied (if not, open additional facilities)
        self._ensure_all_demand_satisfied(
            opened_facilities,
            remaining_demand,
            facility_options,
            solution,
            facility_assignments,
        )

        # Step 5: Build final solution structure
        self._build_solution_structure(opened_facilities, facility_assignments, solution)

        # Step 6: Local improvement (try to reduce costs)
        self._local_improvement(opened_facilities, remaining_demand, solution)

        # Rebuild solution after improvement
        self._build_solution_structure(opened_facilities, facility_assignments, solution)

        # Calculate final objective value
        solution["objective_value"] = (
            solution["total_fixed_cost"] + solution["total_variable_cost"]
        )

        # Add timing and metadata
        elapsed_time = time.time() - start_time
        solution["processing_time"] = elapsed_time
        solution["gap"] = None  # Heuristics don't have gap
        solution["solver_name"] = "Heuristica"

        logger.info(
            f"Heuristic solution found: {len(solution['facilities_opened'])} "
            f"facilities, objective = {solution['objective_value']:.2f}, "
            f"time = {elapsed_time:.2f}s",
        )

        return solution

    def _calculate_facility_options(self) -> List[Dict[str, Any]]:
        """Calculate cost-benefit for each facility-type combination.

        Returns:
            List of facility options with cost-benefit scores.
        """
        options = []

        for j, facility in enumerate(self.facility_points):
            for facility_type, config in CAFETERIA_TYPES.items():
                capacity = config["capacity"]
                fixed_cost = config["fixed_cost"]

                # Calculate average distance to demand points
                avg_distance = sum(self.distance_matrix[i][j] for i in range(len(self.demand_points)))
                avg_distance /= len(self.demand_points) if self.demand_points else 1

                # Cost-benefit: fixed cost per unit capacity + estimated variable cost
                # Lower is better
                cost_per_capacity = fixed_cost / capacity
                estimated_var_cost = avg_distance * DISTANCE_COST_FACTOR
                cost_benefit = cost_per_capacity + estimated_var_cost * 0.1  # Weight variable cost

                options.append({
                    "facility_idx": j,
                    "type": facility_type,
                    "capacity": capacity,
                    "fixed_cost": fixed_cost,
                    "cost_benefit": cost_benefit,
                    "avg_distance": avg_distance,
                })

        return options

    def _assign_demand_to_facility_with_tracking(
        self,
        facility_idx: int,
        facility_type: str,
        available_capacity: float,
        remaining_demand: Dict[int, float],
    ) -> List[Tuple[int, float]]:
        """Assign demand to a facility using greedy approach.

        Args:
            facility_idx: Index of the facility.
            facility_type: Type of the facility.
            available_capacity: Available capacity at the facility.
            remaining_demand: Dictionary of remaining demand per point.

        Returns:
            List of tuples (demand_idx, assigned_amount) for tracking.
        """
        assignments = []

        # Sort demand points by distance to this facility (closer first)
        demand_distances = [
            (i, self.distance_matrix[i][facility_idx], remaining_demand[i])
            for i in remaining_demand.keys()
            if remaining_demand[i] > 1e-6
        ]
        demand_distances.sort(key=lambda x: x[1])  # Sort by distance

        # Assign demand greedily
        for i, distance, demand in demand_distances:
            if available_capacity <= 1e-6:
                break

            assign_amount = min(demand, available_capacity)
            remaining_demand[i] -= assign_amount
            assignments.append((i, assign_amount))
            available_capacity -= assign_amount

        return assignments

    def _ensure_all_demand_satisfied(
        self,
        opened_facilities: Dict[int, Dict[str, Any]],
        remaining_demand: Dict[int, float],
        facility_options: List[Dict[str, Any]],
        solution: Dict[str, Any],
        facility_assignments: Dict[int, List[Tuple[int, float]]],
    ) -> None:
        """Ensure all demand is satisfied by opening additional facilities if needed.

        Args:
            opened_facilities: Dictionary of opened facilities.
            remaining_demand: Dictionary of remaining demand.
            facility_options: List of facility options.
            solution: Solution dictionary to update.
        """
        total_remaining = sum(remaining_demand.values())

        if total_remaining <= 1e-6:
            return  # All demand satisfied

        # Sort options by cost-benefit
        facility_options.sort(key=lambda x: x["cost_benefit"])

        for option in facility_options:
            facility_idx = option["facility_idx"]
            facility_type = option["type"]
            capacity = option["capacity"]
            fixed_cost = option["fixed_cost"]

            # Check if we can use this facility
            if facility_idx in opened_facilities:
                # Use remaining capacity
                used = opened_facilities[facility_idx]["used_capacity"]
                available = capacity - used
            else:
                # Open new facility
                available = capacity
                opened_facilities[facility_idx] = {
                    "type": facility_type,
                    "capacity": capacity,
                    "used_capacity": 0.0,
                    "fixed_cost": fixed_cost,
                }
                solution["total_fixed_cost"] += fixed_cost

            if available > 1e-6:
                assignments = self._assign_demand_to_facility_with_tracking(
                    facility_idx,
                    facility_type,
                    available,
                    remaining_demand,
                )
                if assignments:
                    if facility_idx not in facility_assignments:
                        facility_assignments[facility_idx] = []
                    for demand_idx, assigned_amount in assignments:
                        opened_facilities[facility_idx]["used_capacity"] += assigned_amount
                        facility_assignments[facility_idx].append((demand_idx, assigned_amount))

            total_remaining = sum(remaining_demand.values())
            if total_remaining <= 1e-6:
                break

    def _build_solution_structure(
        self,
        opened_facilities: Dict[int, Dict[str, Any]],
        facility_assignments: Dict[int, List[Tuple[int, float]]],
        solution: Dict[str, Any],
    ) -> None:
        """Build the final solution structure from opened facilities.

        Args:
            opened_facilities: Dictionary of opened facilities.
            facility_assignments: Dictionary tracking assignments per facility.
            solution: Solution dictionary to update.
        """
        solution["facilities_opened"] = []
        solution["assignments"] = {}
        solution["total_variable_cost"] = 0.0

        # Initialize assignments
        for i in range(len(self.demand_points)):
            solution["assignments"][self.demand_points[i]["id"]] = []

        # Build facility list
        for j, facility_info in opened_facilities.items():
            facility = self.facility_points[j]
            solution["facilities_opened"].append({
                "location": facility["id"],
                "type": facility_info["type"],
                "coordinates": (facility["x"], facility["y"]),
                "fixed_cost": facility_info["fixed_cost"],
            })

        # Build assignments from tracking
        for facility_idx, assignments in facility_assignments.items():
            facility = self.facility_points[facility_idx]
            facility_id = facility["id"]

            for demand_idx, assigned_amount in assignments:
                demand_point = self.demand_points[demand_idx]
                demand_id = demand_point["id"]
                distance = self.distance_matrix[demand_idx][facility_idx]
                variable_cost = distance * DISTANCE_COST_FACTOR * assigned_amount

                solution["assignments"][demand_id].append({
                    "facility": facility_id,
                    "fraction": assigned_amount / demand_point["demand"],
                    "assigned_demand": assigned_amount,
                    "variable_cost": variable_cost,
                })
                solution["total_variable_cost"] += variable_cost

    def _local_improvement(
        self,
        opened_facilities: Dict[int, Dict[str, Any]],
        remaining_demand: Dict[int, float],
        solution: Dict[str, Any],
    ) -> None:
        """Try to improve solution with local search.

        Args:
            opened_facilities: Dictionary of opened facilities.
            remaining_demand: Dictionary of remaining demand.
            solution: Solution dictionary to update.
        """
        # Try to close facilities with low utilization
        facilities_to_remove = []
        for j, facility_info in opened_facilities.items():
            utilization = facility_info["used_capacity"] / facility_info["capacity"]
            if utilization < 0.3:  # Less than 30% utilization
                facilities_to_remove.append(j)

        # Try to remove low-utilization facilities and reassign
        for j in facilities_to_remove:
            if j in opened_facilities:
                # Check if demand can be reassigned
                capacity_to_reassign = opened_facilities[j]["used_capacity"]
                can_reassign = False

                for k, other_facility in opened_facilities.items():
                    if k != j:
                        available = other_facility["capacity"] - other_facility["used_capacity"]
                        if available >= capacity_to_reassign:
                            can_reassign = True
                            break

                if can_reassign:
                    # Remove facility
                    solution["total_fixed_cost"] -= opened_facilities[j]["fixed_cost"]
                    del opened_facilities[j]
                    logger.debug(f"Removed low-utilization facility at index {j}")

