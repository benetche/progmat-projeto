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
        # Python < 3.7 compatibility
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

    for facility in solution["facilities_opened"]:
        print(
            f"  - Localizacao: {facility['location']} | "
            f"Tipo: {facility['type']} | "
            f"Coordenadas: ({facility['coordinates'][0]}, {facility['coordinates'][1]}) | "
            f"Custo fixo: {facility['fixed_cost']:.2f}",
        )

    print("\n" + "=" * 80)

