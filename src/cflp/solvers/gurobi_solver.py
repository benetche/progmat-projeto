"""Gurobi solver implementation for CFLP problem.

This module provides the Gurobi-based solver for the Capacitated Facility
Location Problem.
"""

import logging
import time
from typing import Any, Dict, List, Optional

try:
    import gurobipy as gp
    from gurobipy import GRB
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False
    logging.warning("Gurobi not available. Install with: pip install gurobipy")

from src.cflp.config import CAFETERIA_TYPES, DISTANCE_COST_FACTOR

logger = logging.getLogger(__name__)


def is_gurobi_available() -> bool:
    """Check if Gurobi is available.

    Returns:
        True if Gurobi is available, False otherwise.
    """
    return GUROBI_AVAILABLE


class GurobiSolver:
    """Gurobi-based solver for CFLP problem."""

    def __init__(
        self,
        demand_points: List[Dict[str, Any]],
        facility_points: List[Dict[str, Any]],
        distance_matrix: List[List[float]],
    ) -> None:
        """Initialize the Gurobi solver.

        Args:
            demand_points: List of demand point dictionaries.
            facility_points: List of facility location dictionaries.
            distance_matrix: Distance matrix between demand and facility points.
        """
        self.demand_points = demand_points
        self.facility_points = facility_points
        self.distance_matrix = distance_matrix

    def solve(self) -> Optional[Dict[str, Any]]:
        """Solve the CFLP problem using Gurobi.

        Returns:
            Dictionary containing solution information, or None if solver
            is not available or optimization fails.
        """
        if not GUROBI_AVAILABLE:
            logger.error("Gurobi is not available")
            return None

        try:
            # Create model
            model = gp.Model("CFLP_Cantinas")
            model.setParam("OutputFlag", 0)  # Suppress Gurobi output

            # Sets
            I = range(len(self.demand_points))  # Demand points
            J = range(len(self.facility_points))  # Facility locations
            K = list(CAFETERIA_TYPES.keys())  # Cafeteria types

            # Parameters
            d = {i: self.demand_points[i]["demand"] for i in I}  # Demand at point i
            f = {
                (j, k): CAFETERIA_TYPES[k]["fixed_cost"]
                for j in J
                for k in K
            }  # Fixed cost
            Q = {
                k: CAFETERIA_TYPES[k]["capacity"]
                for k in K
            }  # Capacity of cafeteria type k
            c = {
                (i, j): self.distance_matrix[i][j] * DISTANCE_COST_FACTOR
                for i in I
                for j in J
            }  # Variable cost (distance * factor)

            # Decision variables
            # y[j][k] = 1 if facility of type k is opened at location j
            y = model.addVars(
                J,
                K,
                vtype=GRB.BINARY,
                name="y",
            )

            # x[i][j] = fraction of demand at i served by facility at j
            x = model.addVars(
                I,
                J,
                vtype=GRB.CONTINUOUS,
                lb=0.0,
                ub=1.0,
                name="x",
            )

            # Objective: minimize total cost (fixed + variable)
            model.setObjective(
                gp.quicksum(f[j, k] * y[j, k] for j in J for k in K)
                + gp.quicksum(c[i, j] * d[i] * x[i, j] for i in I for j in J),
                GRB.MINIMIZE,
            )

            # Constraints
            # 1. All demand must be satisfied
            for i in I:
                model.addConstr(
                    gp.quicksum(x[i, j] for j in J) == 1.0,
                    name=f"demand_satisfaction_{i}",
                )

            # 2. Capacity constraints: total demand served by a facility
            #    cannot exceed its capacity
            for j in J:
                model.addConstr(
                    gp.quicksum(d[i] * x[i, j] for i in I)
                    <= gp.quicksum(Q[k] * y[j, k] for k in K),
                    name=f"capacity_{j}",
                )

            # 3. At most one cafeteria type per location
            for j in J:
                model.addConstr(
                    gp.quicksum(y[j, k] for k in K) <= 1,
                    name=f"one_type_{j}",
                )

            # 4. Can only assign demand to open facilities
            for i in I:
                for j in J:
                    model.addConstr(
                        x[i, j] <= gp.quicksum(y[j, k] for k in K),
                        name=f"assignment_{i}_{j}",
                    )

            # Optimize with timing
            start_time = time.time()
            model.optimize()
            elapsed_time = time.time() - start_time

            # Extract solution
            status_map = {
                GRB.OPTIMAL: "otima",
                GRB.TIME_LIMIT: "factivel (limite de tempo)",
                GRB.SUBOPTIMAL: "factivel (subotima)",
                GRB.INFEASIBLE: "infactivel",
                GRB.UNBOUNDED: "ilimitada",
                GRB.INF_OR_UNBD: "infactivel ou ilimitada",
            }
            status_str = status_map.get(model.status, f"desconhecido ({model.status})")

            # Calculate gap
            gap = None
            if model.status == GRB.OPTIMAL:
                gap = 0.0
            elif model.status in [GRB.TIME_LIMIT, GRB.SUBOPTIMAL]:
                try:
                    obj_val = model.ObjVal
                    obj_bound = model.ObjBound
                    if obj_bound != float("inf") and obj_bound != 0:
                        gap = abs(obj_val - obj_bound) / abs(obj_bound) * 100
                    elif obj_bound == 0 and obj_val > 0:
                        gap = float("inf")
                except Exception:
                    gap = None

            if model.status in [GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL]:
                solution = self._extract_solution(model, y, x, d, f, c)
                solution["status"] = status_str
                solution["processing_time"] = elapsed_time
                solution["gap"] = gap
                solution["solver_name"] = "Gurobi"
                
                logger.info(
                    f"Gurobi solution found: {len(solution['facilities_opened'])} "
                    f"facilities, objective = {solution['objective_value']:.2f}, "
                    f"time = {elapsed_time:.2f}s",
                )
                return solution
            else:
                logger.error(f"Gurobi optimization failed with status: {model.status}")
                return {
                    "status": status_str,
                    "processing_time": elapsed_time,
                    "gap": gap,
                    "solver_name": "Gurobi",
                }

        except Exception as e:
            logger.error(f"Error solving with Gurobi: {e}")
            return None

    def _extract_solution(
        self,
        model: gp.Model,
        y: Any,
        x: Any,
        d: Dict[int, float],
        f: Dict[tuple, float],
        c: Dict[tuple, float],
    ) -> Dict[str, Any]:
        """Extract solution from Gurobi model.

        Args:
            model: Gurobi model instance.
            y: Binary decision variables for facility opening.
            x: Continuous decision variables for demand assignment.
            d: Demand dictionary.
            f: Fixed cost dictionary.
            c: Variable cost dictionary.

        Returns:
            Dictionary containing solution information.
        """
        I = range(len(self.demand_points))
        J = range(len(self.facility_points))
        K = list(CAFETERIA_TYPES.keys())

        solution = {
            "status": "optimal",
            "objective_value": model.ObjVal,
            "facilities_opened": [],
            "assignments": {},
            "total_fixed_cost": 0.0,
            "total_variable_cost": 0.0,
        }

        # Get opened facilities
        for j in J:
            for k in K:
                if y[j, k].x > 0.5:  # Binary variable is 1
                    facility_id = self.facility_points[j]["id"]
                    solution["facilities_opened"].append({
                        "location": facility_id,
                        "type": k,
                        "coordinates": (
                            self.facility_points[j]["x"],
                            self.facility_points[j]["y"],
                        ),
                        "fixed_cost": f[j, k],
                    })
                    solution["total_fixed_cost"] += f[j, k]

        # Get assignments
        for i in I:
            demand_id = self.demand_points[i]["id"]
            solution["assignments"][demand_id] = []
            for j in J:
                if x[i, j].x > 1e-6:  # Non-zero assignment
                    facility_id = self.facility_points[j]["id"]
                    assigned_demand = d[i] * x[i, j].x
                    variable_cost = c[i, j] * assigned_demand
                    solution["assignments"][demand_id].append({
                        "facility": facility_id,
                        "fraction": x[i, j].x,
                        "assigned_demand": assigned_demand,
                        "variable_cost": variable_cost,
                    })
                    solution["total_variable_cost"] += variable_cost

        return solution

