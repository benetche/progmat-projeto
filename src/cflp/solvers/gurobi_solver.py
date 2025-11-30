"""
Solver usando Gurobi para o problema CFLP.
"""

import logging
import time
from typing import Any, Dict, List, Optional

# Tenta importar Gurobi - se não estiver instalado, o solver não funciona
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

        if not GUROBI_AVAILABLE:
            logger.error("Gurobi is not available")
            return None

        try:
            # Cria o modelo no Gurobi
            model = gp.Model("CFLP_Cantinas")
            # Desliga output do Gurobi para não poluir o console
            model.setParam("OutputFlag", 0)

            # Conjuntos do problema (seguindo notação matemática)
            I = range(len(self.demand_points))  # pontos de demanda
            J = range(len(self.facility_points))  # locais de instalação
            K = list(CAFETERIA_TYPES.keys())  # tipos de cantina

            # Parâmetros do modelo
            # d[i] = demanda no ponto i
            d = {i: self.demand_points[i]["demand"] for i in I}
            # f[j,k] = custo fixo de abrir cantina tipo k no local j
            f = {
                (j, k): CAFETERIA_TYPES[k]["fixed_cost"]
                for j in J
                for k in K
            }
            # Q[k] = capacidade da cantina tipo k
            Q = {
                k: CAFETERIA_TYPES[k]["capacity"]
                for k in K
            }
            # c[i,j] = custo variável por unidade de demanda do ponto i ao local j
            c = {
                (i, j): self.distance_matrix[i][j] * DISTANCE_COST_FACTOR
                for i in I
                for j in J
            }

            # Variáveis de decisão
            # y[j,k] = 1 se abrir cantina tipo k no local j, 0 caso contrário
            y = model.addVars(
                J,
                K,
                vtype=GRB.BINARY,
                name="y",
            )

            # x[i,j] = fração da demanda do ponto i atendida pela cantina no local j
            # Permite divisão de demanda entre múltiplas cantinas (relaxação)
            x = model.addVars(
                I,
                J,
                vtype=GRB.CONTINUOUS,
                lb=0.0,
                ub=1.0,
                name="x",
            )

            # Função objetivo: minimizar custo total
            # Primeiro termo = custos fixos, segundo termo = custos variáveis
            model.setObjective(
                gp.quicksum(f[j, k] * y[j, k] for j in J for k in K)
                + gp.quicksum(c[i, j] * d[i] * x[i, j] for i in I for j in J),
                GRB.MINIMIZE,
            )

            # Restrições do modelo
            # 1. Toda demanda deve ser atendida (soma das frações = 1)
            for i in I:
                model.addConstr(
                    gp.quicksum(x[i, j] for j in J) == 1.0,
                    name=f"demand_satisfaction_{i}",
                )

            # 2. Restrição de capacidade: demanda total atendida por uma cantina
            #    não pode exceder sua capacidade
            for j in J:
                model.addConstr(
                    gp.quicksum(d[i] * x[i, j] for i in I)
                    <= gp.quicksum(Q[k] * y[j, k] for k in K),
                    name=f"capacity_{j}",
                )

            # 3. No máximo um tipo de cantina por local
            for j in J:
                model.addConstr(
                    gp.quicksum(y[j, k] for k in K) <= 1,
                    name=f"one_type_{j}",
                )

            # 4. Só pode atribuir demanda a cantinas abertas
            # Se nenhuma cantina estiver aberta em j, x[i,j] deve ser 0
            for i in I:
                for j in J:
                    model.addConstr(
                        x[i, j] <= gp.quicksum(y[j, k] for k in K),
                        name=f"assignment_{i}_{j}",
                    )

            # Resolve o modelo e mede o tempo
            start_time = time.time()
            model.optimize()
            elapsed_time = time.time() - start_time

            # Mapeia status do Gurobi para texto legível
            status_map = {
                GRB.OPTIMAL: "otima",
                GRB.TIME_LIMIT: "factivel (limite de tempo)",
                GRB.SUBOPTIMAL: "factivel (subotima)",
                GRB.INFEASIBLE: "infactivel",
                GRB.UNBOUNDED: "ilimitada",
                GRB.INF_OR_UNBD: "infactivel ou ilimitada",
            }
            status_str = status_map.get(model.status, f"desconhecido ({model.status})")

            # Calcula gap de optimalidade (diferença entre solução e bound)
            # Gap = 0% significa solução ótima garantida
            gap = None
            if model.status == GRB.OPTIMAL:
                gap = 0.0  # Solução ótima
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

