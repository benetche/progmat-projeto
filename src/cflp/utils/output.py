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
    
    # Status
    status = solution.get("status", "desconhecido")
    print(f"Status da solucao: {status}")
    
    # Objective value
    if "objective_value" in solution:
        print(f"Valor da funcao objetivo: {solution['objective_value']:.2f}")
    
    # Processing time
    if "processing_time" in solution:
        print(f"Tempo de processamento: {solution['processing_time']:.3f} segundos")
    
    # Gap
    if "gap" in solution and solution["gap"] is not None:
        if solution["gap"] == float("inf"):
            print(f"Gap de optimalidade: N/A (bound infinito)")
        else:
            print(f"Gap de optimalidade: {solution['gap']:.4f}%")
    elif "gap" in solution:
        print(f"Gap de optimalidade: N/A (heuristica)")
    
    # Cost breakdown
    if "total_fixed_cost" in solution:
        print(f"Custo fixo total: {solution['total_fixed_cost']:.2f}")
    if "total_variable_cost" in solution:
        print(f"Custo variavel total: {solution['total_variable_cost']:.2f}")
    
    # Facilities
    if "facilities_opened" in solution and solution["facilities_opened"]:
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
    elif "facilities_opened" in solution:
        print(f"\nCantinas abertas: 0 (solucao inviavel ou sem instalacoes)")
        print("-" * 80)

    print("\n" + "=" * 80)


def print_comparison(solutions: Dict[str, Dict[str, Any]]) -> None:
    """Print comparison between all solvers.

    Args:
        solutions: Dictionary mapping solver names to their solutions.
    """
    print("\n" + "=" * 80)
    print("COMPARACAO ENTRE SOLVERS")
    print("=" * 80)

    # Filter out None solutions
    valid_solutions = {k: v for k, v in solutions.items() if v is not None}

    if not valid_solutions:
        print("Nenhuma solucao valida para comparar.")
        print("=" * 80)
        return

    # Find best objective value
    best_obj = None
    best_solver = None
    for solver_name, solution in valid_solutions.items():
        if "objective_value" in solution:
            obj_val = solution["objective_value"]
            if best_obj is None or obj_val < best_obj:
                best_obj = obj_val
                best_solver = solver_name

    # Print comparison table
    print("\nMetricas por Solver:")
    print("-" * 80)
    print(f"{'Solver':<15} {'Status':<25} {'Objetivo':<15} {'Tempo(s)':<12} {'Gap(%)':<12}")
    print("-" * 80)

    for solver_name in sorted(valid_solutions.keys()):
        solution = valid_solutions[solver_name]
        status = solution.get("status", "N/A")
        obj_val = solution.get("objective_value", None)
        time_val = solution.get("processing_time", None)
        gap_val = solution.get("gap", None)

        obj_str = f"{obj_val:.2f}" if obj_val is not None else "N/A"
        time_str = f"{time_val:.3f}" if time_val is not None else "N/A"
        
        if gap_val is None:
            gap_str = "N/A"
        elif gap_val == float("inf"):
            gap_str = "Inf"
        else:
            gap_str = f"{gap_val:.4f}"

        print(f"{solver_name:<15} {status:<25} {obj_str:<15} {time_str:<12} {gap_str:<12}")

    print("-" * 80)

    # Performance comparison
    print("\nComparacao de Desempenho:")
    print("-" * 80)

    # Time comparison
    times = {
        name: sol.get("processing_time")
        for name, sol in valid_solutions.items()
        if sol.get("processing_time") is not None
    }
    if times:
        fastest = min(times.items(), key=lambda x: x[1])
        slowest = max(times.items(), key=lambda x: x[1])
        print(f"Mais rapido: {fastest[0]} ({fastest[1]:.3f}s)")
        print(f"Mais lento: {slowest[0]} ({slowest[1]:.3f}s)")
        if len(times) > 1:
            speedup = slowest[1] / fastest[1]
            print(f"Speedup: {speedup:.2f}x")

    # Solution quality comparison
    print("\nComparacao de Qualidade da Solucao:")
    print("-" * 80)

    objectives = {
        name: sol.get("objective_value")
        for name, sol in valid_solutions.items()
        if sol.get("objective_value") is not None
    }

    if objectives and best_solver:
        print(f"Melhor solucao: {best_solver} (objetivo = {best_obj:.2f})")
        
        for solver_name, obj_val in objectives.items():
            if solver_name != best_solver:
                diff = obj_val - best_obj
                pct_diff = (diff / best_obj) * 100 if best_obj != 0 else 0
                print(f"  {solver_name}: {obj_val:.2f} (diferenca: {diff:+.2f}, {pct_diff:+.2f}%)")

    # Gap analysis
    print("\nAnalise de Gap de Optimalidade:")
    print("-" * 80)
    gaps = {
        name: sol.get("gap")
        for name, sol in valid_solutions.items()
        if sol.get("gap") is not None
    }
    if gaps:
        for solver_name, gap_val in gaps.items():
            if gap_val == 0.0:
                print(f"  {solver_name}: Otima (gap = 0%)")
            elif gap_val == float("inf"):
                print(f"  {solver_name}: Gap infinito (bound nao disponivel)")
            else:
                print(f"  {solver_name}: Gap = {gap_val:.4f}%")
    else:
        print("  Nenhum gap disponivel (apenas heuristica ou solvers nao otimos)")

    # Facilities comparison
    print("\nComparacao de Instalacoes:")
    print("-" * 80)
    facilities_count = {
        name: len(sol.get("facilities_opened", []))
        for name, sol in valid_solutions.items()
        if "facilities_opened" in sol
    }
    if facilities_count:
        for solver_name, count in sorted(facilities_count.items()):
            print(f"  {solver_name}: {count} cantinas abertas")

    print("\n" + "=" * 80)

