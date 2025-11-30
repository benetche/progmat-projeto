"""Output and visualization utilities for CFLP problem.

This module provides functions for displaying and formatting solution results.
"""

import sys
from typing import Any, Dict

# Ensure UTF-8 encoding for output
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")


def print_solution(solution: Dict[str, Any], solver_name: str) -> None:
    """Print solution summary.

    Args:
        solution: Solution dictionary from solver.
        solver_name: Name of the solver used.
    """
    print("\n" + "=" * 80)
    print(f"SOLUCAO CFLP - {solver_name.upper()}")
    print("=" * 80)
    print(f"Status: {solution['status']}")
    print(f"Valor da funcao objetivo: {solution['objective_value']:.2f}")
    print(f"Custo fixo total: {solution['total_fixed_cost']:.2f}")
    print(f"Custo variavel total: {solution['total_variable_cost']:.2f}")
    print(f"\nCantinas abertas: {len(solution['facilities_opened'])}")
    print("-" * 80)

    # Calculate demand coverage for each facility
    facility_demand: Dict[str, Dict[str, Any]] = {}
    for facility in solution["facilities_opened"]:
        facility_id = facility["location"]
        facility_demand[facility_id] = {
            "total_demand": 0.0,
            "demand_points": [],
        }

    # Process assignments to calculate demand per facility
    for demand_id, assignments in solution.get("assignments", {}).items():
        for assignment in assignments:
            facility_id = assignment["facility"]
            if facility_id in facility_demand:
                facility_demand[facility_id]["total_demand"] += assignment["assigned_demand"]
                facility_demand[facility_id]["demand_points"].append({
                    "id": demand_id,
                    "demand": assignment["assigned_demand"],
                    "fraction": assignment["fraction"],
                })

    # Print facilities with demand information
    for facility in solution["facilities_opened"]:
        facility_id = facility["location"]
        demand_info = facility_demand[facility_id]
        
        print(
            f"\n  - Localizacao: {facility_id} | "
            f"Tipo: {facility['type']} | "
            f"Coordenadas: ({facility['coordinates'][0]}, {facility['coordinates'][1]}) | "
            f"Custo fixo: {facility['fixed_cost']:.2f}",
        )
        print(f"    Demanda coberta: {demand_info['total_demand']:.2f}")
        print(f"    Pontos de demanda atendidos: {len(demand_info['demand_points'])}")
        
        # List demand points (limit to first 15 for readability)
        if demand_info["demand_points"]:
            demand_points_list = demand_info["demand_points"][:15]
            points_str = ", ".join([
                f"{dp['id']}({dp['demand']:.1f})"
                for dp in demand_points_list
            ])
            if len(demand_info["demand_points"]) > 15:
                points_str += f", ... (+{len(demand_info['demand_points']) - 15} mais)"
            print(f"    Pontos de demanda: {points_str}")

    print("\n" + "=" * 80)

