"""
Heurística gulosa para resolver o problema CFLP.
"""

import logging
import time
from typing import Any, Dict, List, Tuple

from src.cflp.config import CAFETERIA_TYPES, DISTANCE_COST_FACTOR

logger = logging.getLogger(__name__)


class HeuristicSolver:

    def __init__(
        self,
        demand_points: List[Dict[str, Any]],
        facility_points: List[Dict[str, Any]],
        distance_matrix: List[List[float]],
    ) -> None:
        self.demand_points = demand_points
        self.facility_points = facility_points
        self.distance_matrix = distance_matrix

    def solve(self) -> Dict[str, Any]:

        logger.info("Starting heuristic solution construction")
        start_time = time.time()

        # Estrutura inicial da solução
        solution = {
            "status": "heuristic",
            "objective_value": 0.0,
            "facilities_opened": [],
            "assignments": {},
            "total_fixed_cost": 0.0,
            "total_variable_cost": 0.0,
        }

        # Calcula demanda total (útil para debug, mas não usado diretamente)
        total_demand = sum(point["demand"] for point in self.demand_points)

        # Etapa 1: Calcula score de custo-benefício para cada opção
        facility_options = self._calculate_facility_options()

        # Etapa 2: Ordena por score (menor = melhor)
        facility_options.sort(key=lambda x: x["cost_benefit"])

        # Etapa 3: Construção gulosa
        # Guarda quais cantinas foram abertas: índice -> {tipo, capacidade, capacidade_usada}
        opened_facilities: Dict[int, Dict[str, Any]] = {}
        # Demanda que ainda precisa ser atendida
        remaining_demand = {i: self.demand_points[i]["demand"] for i in range(len(self.demand_points))}
        # Rastreia atribuições: índice_cantina -> lista de (índice_demanda, quantidade_atribuída)
        facility_assignments: Dict[int, List[Tuple[int, float]]] = {}

        # Percorre as opções ordenadas por score
        for option in facility_options:
            facility_idx = option["facility_idx"]
            facility_type = option["type"]
            capacity = option["capacity"]
            fixed_cost = option["fixed_cost"]

            # Pula se já abriu uma cantina neste local
            if facility_idx in opened_facilities:
                continue

            # Tenta atribuir demanda a esta cantina
            # Começa com toda a capacidade disponível
            available_capacity = capacity

            assignments = self._assign_demand_to_facility_with_tracking(
                facility_idx,
                facility_type,
                available_capacity,
                remaining_demand,
            )

            # Se conseguiu atribuir alguma demanda, abre a cantina
            if assignments:
                opened_facilities[facility_idx] = {
                    "type": facility_type,
                    "capacity": capacity,
                    "used_capacity": 0.0,
                    "fixed_cost": fixed_cost,
                }
                solution["total_fixed_cost"] += fixed_cost
                facility_assignments[facility_idx] = []

                # Registra as atribuições
                for demand_idx, assigned_amount in assignments:
                    opened_facilities[facility_idx]["used_capacity"] += assigned_amount
                    facility_assignments[facility_idx].append((demand_idx, assigned_amount))

        # Etapa 4: Garante que toda demanda seja atendida
        # Se sobrou demanda, abre cantinas adicionais se necessário
        self._ensure_all_demand_satisfied(
            opened_facilities,
            remaining_demand,
            facility_options,
            solution,
            facility_assignments,
        )

        # Etapa 5: Constrói estrutura final da solução
        self._build_solution_structure(opened_facilities, facility_assignments, solution)

        # Etapa 6: Melhoria local - tenta remover cantinas pouco utilizadas
        self._local_improvement(opened_facilities, remaining_demand, solution)

        # Reconstrói solução após melhorias (pode ter removido cantinas)
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

        options = []

        for j, facility in enumerate(self.facility_points):
            for facility_type, config in CAFETERIA_TYPES.items():
                capacity = config["capacity"]
                fixed_cost = config["fixed_cost"]

                # Calcula distância média até os pontos de demanda
                # Isso dá uma ideia de quão "central" é o local
                avg_distance = sum(self.distance_matrix[i][j] for i in range(len(self.demand_points)))
                avg_distance /= len(self.demand_points) if self.demand_points else 1

                # Score de custo-benefício
                # Primeiro termo: custo fixo por unidade de capacidade
                # Segundo termo: estimativa de custo variável (peso menor)
                cost_per_capacity = fixed_cost / capacity
                estimated_var_cost = avg_distance * DISTANCE_COST_FACTOR
                # Peso 0.1 no custo variável porque é só uma estimativa
                cost_benefit = cost_per_capacity + estimated_var_cost * 0.1

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

        assignments = []

        # Ordena pontos de demanda por distância (mais próximos primeiro)
        # Filtra apenas pontos com demanda restante > 0
        demand_distances = [
            (i, self.distance_matrix[i][facility_idx], remaining_demand[i])
            for i in remaining_demand.keys()
            if remaining_demand[i] > 1e-6
        ]
        demand_distances.sort(key=lambda x: x[1])  # Ordena por distância

        # Atribui demanda de forma gulosa (mais próximo primeiro)
        for i, distance, demand in demand_distances:
            if available_capacity <= 1e-6:
                break  # Sem capacidade disponível

            # Atribui o máximo possível (demanda restante ou capacidade disponível)
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

        total_remaining = sum(remaining_demand.values())

        if total_remaining <= 1e-6:
            return  # Toda demanda já foi atendida

        # Reordena opções por score (pode ter mudado após primeira passada)
        facility_options.sort(key=lambda x: x["cost_benefit"])

        for option in facility_options:
            facility_idx = option["facility_idx"]
            facility_type = option["type"]
            capacity = option["capacity"]
            fixed_cost = option["fixed_cost"]

            # Verifica se pode usar esta cantina
            if facility_idx in opened_facilities:
                # Usa capacidade restante da cantina já aberta
                used = opened_facilities[facility_idx]["used_capacity"]
                available = capacity - used
            else:
                # Abre nova cantina
                available = capacity
                opened_facilities[facility_idx] = {
                    "type": facility_type,
                    "capacity": capacity,
                    "used_capacity": 0.0,
                    "fixed_cost": fixed_cost,
                }
                solution["total_fixed_cost"] += fixed_cost

            # Tenta atribuir demanda se houver capacidade
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

            # Verifica se ainda sobra demanda
            total_remaining = sum(remaining_demand.values())
            if total_remaining <= 1e-6:
                break  # Toda demanda atendida, pode parar

    def _build_solution_structure(
        self,
        opened_facilities: Dict[int, Dict[str, Any]],
        facility_assignments: Dict[int, List[Tuple[int, float]]],
        solution: Dict[str, Any],
    ) -> None:

        solution["facilities_opened"] = []
        solution["assignments"] = {}
        solution["total_variable_cost"] = 0.0

        # Inicializa estrutura de atribuições
        for i in range(len(self.demand_points)):
            solution["assignments"][self.demand_points[i]["id"]] = []

        # Constrói lista de cantinas abertas
        for j, facility_info in opened_facilities.items():
            facility = self.facility_points[j]
            solution["facilities_opened"].append({
                "location": facility["id"],
                "type": facility_info["type"],
                "coordinates": (facility["x"], facility["y"]),
                "fixed_cost": facility_info["fixed_cost"],
            })

        # Constrói atribuições a partir do rastreamento interno
        for facility_idx, assignments in facility_assignments.items():
            facility = self.facility_points[facility_idx]
            facility_id = facility["id"]

            for demand_idx, assigned_amount in assignments:
                demand_point = self.demand_points[demand_idx]
                demand_id = demand_point["id"]
                distance = self.distance_matrix[demand_idx][facility_idx]
                # Custo variável = distância × fator × demanda atribuída
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

        # Identifica cantinas com baixa utilização (< 30%)
        facilities_to_remove = []
        for j, facility_info in opened_facilities.items():
            utilization = facility_info["used_capacity"] / facility_info["capacity"]
            if utilization < 0.3:  # Menos de 30% de utilização
                facilities_to_remove.append(j)

        # Tenta remover cantinas pouco utilizadas
        for j in facilities_to_remove:
            if j in opened_facilities:
                # Verifica se a demanda pode ser realocada
                capacity_to_reassign = opened_facilities[j]["used_capacity"]
                can_reassign = False

                # Procura outras cantinas com capacidade suficiente
                for k, other_facility in opened_facilities.items():
                    if k != j:
                        available = other_facility["capacity"] - other_facility["used_capacity"]
                        if available >= capacity_to_reassign:
                            can_reassign = True
                            break

                # Se conseguiu realocar, remove a cantina (economiza custo fixo)
                if can_reassign:
                    solution["total_fixed_cost"] -= opened_facilities[j]["fixed_cost"]
                    del opened_facilities[j]
                    logger.debug(f"Removed low-utilization facility at index {j}")

