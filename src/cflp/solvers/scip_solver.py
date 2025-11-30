"""SCIP solver implementation for CFLP problem.

This module provides the SCIP-based solver for the Capacitated Facility
Location Problem.
"""

import logging
import time
from typing import Any, Dict, List, Optional

try:
    from pyscipopt import Model, quicksum
    SCIP_AVAILABLE = True
except ImportError:
    SCIP_AVAILABLE = False
    logging.warning("SCIP not available. Install with: pip install pyscipopt")

from src.cflp.config import CAFETERIA_TYPES, DISTANCE_COST_FACTOR

logger = logging.getLogger(__name__)


def is_scip_available() -> bool:
    """Check if SCIP is available.

    Returns:
        True if SCIP is available, False otherwise.
    """
    return SCIP_AVAILABLE


class SCIPSolver:
    """SCIP-based solver for CFLP problem."""

    def __init__(
        self,
        demand_points: List[Dict[str, Any]],
        facility_points: List[Dict[str, Any]],
        distance_matrix: List[List[float]],
    ) -> None:
        """Initialize the SCIP solver.

        Args:
            demand_points: List of demand point dictionaries.
            facility_points: List of facility location dictionaries.
            distance_matrix: Distance matrix between demand and facility points.
        """
        self.demand_points = demand_points
        self.facility_points = facility_points
        self.distance_matrix = distance_matrix

    def solve(self) -> Optional[Dict[str, Any]]:
        """Solve the CFLP problem using SCIP.

        Returns:
            Dictionary containing solution information, or None if solver
            is not available or optimization fails.
        """
        if not SCIP_AVAILABLE:
            logger.error("SCIP is not available")
            return None

        try:
            # Create model
            model = Model("CFLP_Cantinas")
            model.hideOutput()  # Suppress SCIP output

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
            y = {}
            for j in J:
                for k in K:
                    y[j, k] = model.addVar(
                        vtype="B",
                        name=f"y_{j}_{k}",
                    )

            # x[i][j] = fraction of demand at i served by facility at j
            x = {}
            for i in I:
                for j in J:
                    x[i, j] = model.addVar(
                        vtype="C",
                        lb=0.0,
                        ub=1.0,
                        name=f"x_{i}_{j}",
                    )

            # Objective: minimize total cost (fixed + variable)
            model.setObjective(
                quicksum(f[j, k] * y[j, k] for j in J for k in K)
                + quicksum(c[i, j] * d[i] * x[i, j] for i in I for j in J),
                "minimize",
            )

            # Constraints
            # 1. All demand must be satisfied
            for i in I:
                model.addCons(
                    quicksum(x[i, j] for j in J) == 1.0,
                    name=f"demand_satisfaction_{i}",
                )

            # 2. Capacity constraints: total demand served by a facility
            #    cannot exceed its capacity
            for j in J:
                model.addCons(
                    quicksum(d[i] * x[i, j] for i in I)
                    <= quicksum(Q[k] * y[j, k] for k in K),
                    name=f"capacity_{j}",
                )

            # 3. At most one cafeteria type per location
            for j in J:
                model.addCons(
                    quicksum(y[j, k] for k in K) <= 1,
                    name=f"one_type_{j}",
                )

            # 4. Can only assign demand to open facilities
            for i in I:
                for j in J:
                    model.addCons(
                        x[i, j] <= quicksum(y[j, k] for k in K),
                        name=f"assignment_{i}_{j}",
                    )

            # Optimize with timing
            start_time = time.time()
            model.optimize()
            elapsed_time = time.time() - start_time

            # Get status
            scip_status = model.getStatus()
            status_map = {
                "optimal": "otima",
                "timelimit": "factivel (limite de tempo)",
                "infeasible": "infactivel",
                "unbounded": "ilimitada",
                "inforunbd": "infactivel ou ilimitada",
            }
            status_str = status_map.get(scip_status, f"desconhecido ({scip_status})")

            # Calculate gap
            gap = None
            if scip_status == "optimal":
                gap = 0.0
            elif scip_status == "timelimit":
                try:
                    obj_val = model.getObjVal()
                    dual_bound = model.getDualbound()
                    if dual_bound != float("inf") and dual_bound != 0:
                        gap = abs(obj_val - dual_bound) / abs(dual_bound) * 100
                    elif dual_bound == 0 and obj_val > 0:
                        gap = float("inf")
                except Exception:
                    gap = None

            if scip_status in ["optimal", "timelimit"]:
                solution = self._extract_solution(model, y, x, d, f, c)
                solution["status"] = status_str
                solution["processing_time"] = elapsed_time
                solution["gap"] = gap
                solution["solver_name"] = "SCIP"
                
                logger.info(
                    f"SCIP solution found: {len(solution['facilities_opened'])} "
                    f"facilities, objective = {solution['objective_value']:.2f}, "
                    f"time = {elapsed_time:.2f}s",
                )
                return solution
            else:
                logger.error(f"SCIP optimization failed with status: {scip_status}")
                return {
                    "status": status_str,
                    "processing_time": elapsed_time,
                    "gap": gap,
                    "solver_name": "SCIP",
                }

        except Exception as e:
            logger.error(f"Error solving with SCIP: {e}")
            return None

    def _extract_solution(
        self,
        model: Model,
        y: Dict[tuple, Any],
        x: Dict[tuple, Any],
        d: Dict[int, float],
        f: Dict[tuple, float],
        c: Dict[tuple, float],
    ) -> Dict[str, Any]:
        """Extract solution from SCIP model.

        Args:
            model: SCIP model instance.
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
            "objective_value": model.getObjVal(),
            "facilities_opened": [],
            "assignments": {},
            "total_fixed_cost": 0.0,
            "total_variable_cost": 0.0,
        }

        # Get opened facilities
        for j in J:
            for k in K:
                if model.getVal(y[j, k]) > 0.5:  # Binary variable is 1
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
                x_val = model.getVal(x[i, j])
                if x_val > 1e-6:  # Non-zero assignment
                    facility_id = self.facility_points[j]["id"]
                    assigned_demand = d[i] * x_val
                    variable_cost = c[i, j] * assigned_demand
                    solution["assignments"][demand_id].append({
                        "facility": facility_id,
                        "fraction": x_val,
                        "assigned_demand": assigned_demand,
                        "variable_cost": variable_cost,
                    })
                    solution["total_variable_cost"] += variable_cost

        return solution

