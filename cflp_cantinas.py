"""
Script principal para resolver o problema CFLP de otimização de cantinas.

"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Ajuste de encoding para evitar problemas com caracteres especiais no Windows
# Tentei usar reconfigure primeiro, mas em versões antigas do Python precisa do fallback
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        # Fallback para Python < 3.7
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

    try:
        # Carrega os dados do JSON - pontos de demanda e locais possíveis
        demand_points, facility_points = load_points(JSON_PATH)

        # Validações básicas antes de continuar
        if not demand_points:
            print("Erro: Nenhum ponto de demanda encontrado.")
            return

        if not facility_points:
            print("Erro: Nenhum ponto de instalacao encontrado.")
            return

        # Pre-calcula a matriz de distâncias uma vez só (evita recalcular várias vezes)
        distance_matrix = calculate_distance_matrix(demand_points, facility_points)

        # Guarda todas as soluções para comparar no final
        all_solutions: Dict[str, Any] = {}

        # Tenta resolver com Gurobi (se disponível)
        # Gurobi geralmente é mais rápido, então tento primeiro
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

        # SCIP como alternativa open-source
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

        # Heurística sempre roda (não precisa de biblioteca externa)
        # Útil para ter uma solução rápida mesmo sem os solvers exatos
        print("\n" + "=" * 80)
        print("RESOLVENDO COM HEURISTICA...")
        print("=" * 80)
        heuristic_solver = HeuristicSolver(demand_points, facility_points, distance_matrix)
        heuristic_solution = heuristic_solver.solve()
        if heuristic_solution:
            print_solution(heuristic_solution, "Heuristica")
            all_solutions["Heuristica"] = heuristic_solution

        # Só mostra comparação se tiver pelo menos 2 soluções
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
