"""Main entry point for CFLP problem solving.

This module provides the main entry point for solving the Capacitated Facility
Location Problem (CFLP) for optimizing cafeteria construction in a university campus.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure UTF-8 encoding for output
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        # Python < 3.7 compatibility
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

from src.cflp.config import JSON_PATH
from src.cflp.data_loader import load_points
from src.cflp.distance import calculate_distance_matrix
from src.cflp.solvers import (
    GurobiSolver,
    HeuristicSolver,
    SCIPSolver,
    is_gurobi_available,
    is_scip_available,
)
from src.cflp.utils.output import print_comparison, print_solution

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for CFLP problem solving."""
    try:
        # Load data
        demand_points, facility_points = load_points(JSON_PATH)

        if not demand_points:
            print("Erro: Nenhum ponto de demanda encontrado.")
            return

        if not facility_points:
            print("Erro: Nenhum ponto de instalacao encontrado.")
            return

        # Calculate distance matrix
        distance_matrix = calculate_distance_matrix(demand_points, facility_points)

        # Store all solutions for comparison
        all_solutions: Dict[str, Any] = {}

        # Solve with Gurobi
        if is_gurobi_available():
            print("\n" + "=" * 80)
            print("RESOLVENDO COM GUROBI...")
            print("=" * 80)
            gurobi_solver = GurobiSolver(demand_points, facility_points, distance_matrix)
            gurobi_solution = gurobi_solver.solve()
            if gurobi_solution:
                print_solution(gurobi_solution, "Gurobi")
                all_solutions["Gurobi"] = gurobi_solution
        else:
            print("\nGurobi nao esta disponivel. Instale com: pip install gurobipy")

        # Solve with SCIP
        if is_scip_available():
            print("\n" + "=" * 80)
            print("RESOLVENDO COM SCIP...")
            print("=" * 80)
            scip_solver = SCIPSolver(demand_points, facility_points, distance_matrix)
            scip_solution = scip_solver.solve()
            if scip_solution:
                print_solution(scip_solution, "SCIP")
                all_solutions["SCIP"] = scip_solution
        else:
            print("\nSCIP nao esta disponivel. Instale com: pip install pyscipopt")

        # Solve with Heuristic
        print("\n" + "=" * 80)
        print("RESOLVENDO COM HEURISTICA...")
        print("=" * 80)
        heuristic_solver = HeuristicSolver(demand_points, facility_points, distance_matrix)
        heuristic_solution = heuristic_solver.solve()
        if heuristic_solution:
            print_solution(heuristic_solution, "Heuristica")
            all_solutions["Heuristica"] = heuristic_solution

        # Print comparison
        if len(all_solutions) > 1:
            print_comparison(all_solutions)

    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        print(f"\nErro: Arquivo nao encontrado: {e}\n")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {e}")
        print(f"\nErro: Arquivo JSON invalido: {e}\n")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nErro inesperado: {e}\n")


if __name__ == "__main__":
    main()
