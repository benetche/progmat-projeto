"""
Funções para exibir os resultados das soluções.

Formata e imprime as soluções de forma legível, incluindo métricas
importantes como custos, tempo de processamento e gap de optimalidade.
"""

import sys
from typing import Any, Dict

# Ajuste de encoding (mesma lógica do arquivo principal)
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")


def print_solution(solution: Dict[str, Any], solver_name: str) -> None:
    """
    Imprime resumo completo da solução encontrada.

    Mostra status, custos, cantinas abertas e detalhes de cada instalação.
    """
    print("\n" + "=" * 80)
    print(f"SOLUCAO CFLP - {solver_name.upper()}")
    print("=" * 80)
    
    # Status da solução (ótima, factível, etc.)
    status = solution.get("status", "desconhecido")
    print(f"Status da solucao: {status}")
    
    # Valor da função objetivo (custo total)
    if "objective_value" in solution:
        print(f"Valor da funcao objetivo: {solution['objective_value']:.2f}")
    
    # Tempo que o solver levou para resolver
    if "processing_time" in solution:
        print(f"Tempo de processamento: {solution['processing_time']:.3f} segundos")
    
    # Gap de optimalidade (só faz sentido para solvers exatos)
    # Gap = 0% significa solução ótima garantida
    if "gap" in solution and solution["gap"] is not None:
        if solution["gap"] == float("inf"):
            print(f"Gap de optimalidade: N/A (bound infinito)")
        else:
            print(f"Gap de optimalidade: {solution['gap']:.4f}%")
    elif "gap" in solution:
        print(f"Gap de optimalidade: N/A (heuristica)")
    
    # Breakdown de custos
    if "total_fixed_cost" in solution:
        print(f"Custo fixo total: {solution['total_fixed_cost']:.2f}")
    if "total_variable_cost" in solution:
        print(f"Custo variavel total: {solution['total_variable_cost']:.2f}")
    
    # Detalhes das cantinas abertas
    if "facilities_opened" in solution and solution["facilities_opened"]:
        print(f"\nCantinas abertas: {len(solution['facilities_opened'])}")
        print("-" * 80)

        # Agrega informações de demanda por cantina
        # Preciso processar as atribuições para saber quanto cada cantina atende
        facility_demand: Dict[str, Dict[str, Any]] = {}
        for facility in solution["facilities_opened"]:
            facility_id = facility["location"]
            facility_demand[facility_id] = {
                "total_demand": 0.0,
                "total_variable_cost": 0.0,
                "demand_points": [],
            }

        # Percorre todas as atribuições e agrupa por cantina
        for demand_id, assignments in solution.get("assignments", {}).items():
            for assignment in assignments:
                facility_id = assignment["facility"]
                if facility_id in facility_demand:
                    # Soma a demanda e custo variável
                    facility_demand[facility_id]["total_demand"] += assignment["assigned_demand"]
                    facility_demand[facility_id]["total_variable_cost"] += assignment.get("variable_cost", 0.0)
                    # Guarda quais pontos são atendidos
                    facility_demand[facility_id]["demand_points"].append({
                        "id": demand_id,
                        "demand": assignment["assigned_demand"],
                        "fraction": assignment["fraction"],
                    })

        # Imprime detalhes de cada cantina
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
            print(f"    Custo variavel: {demand_info['total_variable_cost']:.2f}")
            print(f"    Pontos de demanda atendidos: {len(demand_info['demand_points'])}")
            
            # Lista os pontos atendidos (limito a 15 para não poluir o output)
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
    """
    Compara as soluções de todos os solvers executados.

    Mostra tabela comparativa e análises de desempenho e qualidade.
    """
    print("\n" + "=" * 80)
    print("COMPARACAO ENTRE SOLVERS")
    print("=" * 80)

    # Remove soluções None (caso algum solver tenha falhado)
    valid_solutions = {k: v for k, v in solutions.items() if v is not None}

    if not valid_solutions:
        print("Nenhuma solucao valida para comparar.")
        print("=" * 80)
        return

    # Encontra a melhor solução (menor valor objetivo)
    best_obj = None
    best_solver = None
    for solver_name, solution in valid_solutions.items():
        if "objective_value" in solution:
            obj_val = solution["objective_value"]
            if best_obj is None or obj_val < best_obj:
                best_obj = obj_val
                best_solver = solver_name

    # Tabela com métricas principais
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

        # Formatação dos valores (trata None e infinito)
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

    # Análise de desempenho (tempo de processamento)
    print("\nComparacao de Desempenho:")
    print("-" * 80)

    # Coleta tempos de todos os solvers
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
        # Calcula speedup (evita divisão por zero)
        if len(times) > 1 and fastest[1] > 1e-6:
            speedup = slowest[1] / fastest[1]
            print(f"Speedup: {speedup:.2f}x")
        elif len(times) > 1:
            print(f"Speedup: N/A (tempo mais rapido muito proximo de zero)")

    # Comparação de qualidade (valor objetivo)
    print("\nComparacao de Qualidade da Solucao:")
    print("-" * 80)

    objectives = {
        name: sol.get("objective_value")
        for name, sol in valid_solutions.items()
        if sol.get("objective_value") is not None
    }

    if objectives and best_solver:
        print(f"Melhor solucao: {best_solver} (objetivo = {best_obj:.2f})")
        
        # Mostra diferença percentual em relação à melhor
        for solver_name, obj_val in objectives.items():
            if solver_name != best_solver:
                diff = obj_val - best_obj
                # Evita divisão por zero
                pct_diff = (diff / best_obj) * 100 if best_obj != 0 else 0
                print(f"  {solver_name}: {obj_val:.2f} (diferenca: {diff:+.2f}, {pct_diff:+.2f}%)")

    # Análise de gap (só para solvers exatos)
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

    # Comparação de número de instalações
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

