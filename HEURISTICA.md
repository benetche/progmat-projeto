# Heurística para o Problema CFLP

## Visão Geral

A heurística implementada é uma **solução gulosa (greedy)** com melhorias locais para resolver o problema CFLP (Capacitated Facility Location Problem). Esta abordagem fornece uma solução viável de forma rápida, embora não garanta optimalidade.

## Estrutura da Implementação

A heurística está implementada no arquivo `src/cflp/solvers/heuristic_solver.py` e consiste na classe `HeuristicSolver`, que segue a mesma interface dos solvers exatos (Gurobi e SCIP).

## Algoritmo

### Fase 1: Cálculo de Custo-Benefício

Para cada combinação de (localização, tipo de cantina), calcula-se um **score de custo-benefício**:

```python
cost_per_capacity = fixed_cost / capacity
estimated_var_cost = avg_distance * DISTANCE_COST_FACTOR
cost_benefit = cost_per_capacity + estimated_var_cost * 0.1
```

Onde:

- `cost_per_capacity`: Custo fixo por unidade de capacidade
- `estimated_var_cost`: Estimativa do custo variável baseado na distância média
- `cost_benefit`: Score final (menor é melhor)

### Fase 2: Ordenação Gulosa

Todas as opções (localização, tipo) são ordenadas por custo-benefício em ordem crescente. Isso prioriza:

1. Cantinas com menor custo fixo por unidade de capacidade
2. Cantinas mais próximas dos pontos de demanda (em média)

### Fase 3: Construção da Solução

A solução é construída iterativamente:

1. **Seleção Gulosa**: Para cada opção ordenada:

   - Se a instalação ainda não foi aberta, considera abri-la
   - Calcula quanto de demanda pode ser atendida

2. **Atribuição de Demanda**: Para cada instalação aberta:

   - Ordena pontos de demanda por distância (mais próximos primeiro)
   - Atribui demanda de forma gulosa até esgotar a capacidade
   - Atualiza a demanda restante

3. **Garantia de Viabilidade**: Se ainda houver demanda não atendida:
   - Abre instalações adicionais conforme necessário
   - Continua até toda demanda ser satisfeita

### Fase 4: Melhoria Local

Após construir a solução inicial, aplica-se uma **busca local**:

1. **Remoção de Instalações Subutilizadas**:

   - Identifica instalações com utilização < 30%
   - Verifica se a demanda pode ser realocada para outras instalações
   - Remove instalações se possível, reduzindo custos fixos

2. **Reatribuição**: Recalcula as atribuições de demanda após remoções

### Fase 5: Construção Final da Estrutura

A solução final é estruturada:

1. **Lista de Instalações Abertas**: Todas as instalações que permaneceram abertas
2. **Atribuições de Demanda**: Para cada ponto de demanda:
   - Identifica a instalação mais próxima com capacidade disponível
   - Atribui demanda de forma a minimizar distância
   - Calcula custos variáveis

## Características da Heurística

### Vantagens

1. **Rapidez**: Executa em tempo polinomial O(n² × m × k), onde:

   - n = número de pontos de demanda
   - m = número de locais de instalação
   - k = número de tipos de cantinas

2. **Simplicidade**: Fácil de implementar e entender

3. **Viabilidade Garantida**: Sempre produz uma solução viável

4. **Sem Dependências Externas**: Não requer solvers comerciais

### Limitações

1. **Não Garante Optimalidade**: A solução pode não ser ótima

2. **Decisões Locais**: Escolhas baseadas apenas em informações locais

3. **Pode Subutilizar Instalações**: Pode abrir mais instalações do que o necessário

## Complexidade

- **Tempo**: O(n² × m × k) no pior caso
- **Espaço**: O(n × m) para armazenar matriz de distâncias

## Comparação com Solvers Exatos

| Aspecto                  | Heurística                 | Gurobi/SCIP                     |
| ------------------------ | -------------------------- | ------------------------------- |
| Tempo de execução        | Rápido (segundos)          | Mais lento (pode levar minutos) |
| Qualidade da solução     | Boa (não ótima)            | Ótima                           |
| Garantia de optimalidade | Não                        | Sim                             |
| Dependências             | Nenhuma                    | Requer solver instalado         |
| Escalabilidade           | Boa para problemas grandes | Limitada por recursos           |

## Uso

A heurística pode ser executada junto com os solvers exatos:

```bash
python cflp_cantinas.py
```

A saída incluirá a solução heurística após as soluções dos solvers exatos (se disponíveis).

## Estrutura do Código

```
src/cflp/solvers/
├── heuristic_solver.py
│   └── HeuristicSolver
│       ├── __init__()          # Inicialização
│       ├── solve()              # Método principal
│       ├── _calculate_facility_options()      # Fase 1
│       ├── _assign_demand_to_facility()       # Fase 3.2
│       ├── _ensure_all_demand_satisfied()     # Fase 3.3
│       ├── _build_solution_structure()        # Fase 5
│       └── _local_improvement()               # Fase 4
```

## Exemplo de Execução

```
================================================================================
RESOLVENDO COM HEURISTICA...
================================================================================
SOLUCAO CFLP - HEURISTICA
================================================================================
Status: heuristic
Valor da funcao objetivo: 2150000.00
Custo fixo total: 1100000.00
Custo variavel total: 1050000.00

Cantinas abertas: 10
--------------------------------------------------------------------------------

  - Localizacao: C3 | Tipo: media | Coordenadas: (1319, 2308) | Custo fixo: 110000.00
    Demanda coberta: 550.00
    Pontos de demanda atendidos: 12
    Pontos de demanda: 1(50.0), 2(52.0), 3(30.0), ...
...
```

## Melhorias Futuras

Possíveis extensões da heurística:

1. **Busca Tabu**: Evitar ciclos e explorar melhor o espaço de soluções
2. **Simulated Annealing**: Aceitar soluções piores temporariamente
3. **Algoritmo Genético**: Evolução de populações de soluções
4. **GRASP (Greedy Randomized Adaptive Search Procedure)**: Adicionar aleatoriedade controlada
5. **VND (Variable Neighborhood Descent)**: Múltiplas estruturas de vizinhança

## Conclusão

A heurística implementada oferece uma alternativa rápida e viável aos solvers exatos, sendo especialmente útil para:

- Problemas muito grandes onde solvers exatos são lentos
- Análises exploratórias rápidas
- Validação de soluções
- Ambientes sem acesso a solvers comerciais
