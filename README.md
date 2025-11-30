# Projeto CFLP - Otimização de Cantinas em Campus Universitário

Este projeto implementa um problema de **Capacitated Facility Location Problem (CFLP)** para otimizar a construção de cantinas em um campus universitário.

## Estrutura do Projeto

```
projeto-progmat/
├── src/
│   ├── __init__.py
│   └── cflp/
│       ├── __init__.py              # Módulo principal CFLP
│       ├── config.py                 # Configurações e constantes
│       ├── data_loader.py            # Carregamento de dados JSON
│       ├── distance.py               # Cálculo de distâncias
│       ├── solvers/
│       │   ├── __init__.py
│       │   ├── gurobi_solver.py     # Implementação do solver Gurobi
│       │   └── scip_solver.py        # Implementação do solver SCIP
│       └── utils/
│           ├── __init__.py
│           └── output.py            # Visualização de resultados
├── cflp_cantinas.py                  # Ponto de entrada principal
├── calculate_total_demand.py         # Script auxiliar para calcular demanda
├── map_point_marker.py               # Interface gráfica para marcar pontos
├── map_points.json                   # Dados dos pontos (demanda e instalação)
├── requirements.txt                  # Dependências do projeto
└── RELATORIO_CFLP.md                 # Relatório completo da implementação
```

## Módulos

### `src/cflp/config.py`
Contém todas as configurações e constantes:
- Tipos de cantinas (pequena, média, grande) com capacidades e custos
- Fator de custo por distância
- Caminho do arquivo JSON

### `src/cflp/data_loader.py`
Responsável por carregar dados do arquivo JSON:
- `load_points()`: Carrega pontos de demanda e instalação

### `src/cflp/distance.py`
Funções para cálculo de distâncias:
- `calculate_euclidean_distance()`: Calcula distância euclidiana entre dois pontos
- `calculate_distance_matrix()`: Cria matriz de distâncias entre todos os pares

### `src/cflp/solvers/`
Implementações dos solvers de otimização:

#### `gurobi_solver.py`
- `GurobiSolver`: Classe para resolver o problema com Gurobi
- `is_gurobi_available()`: Verifica disponibilidade do Gurobi

#### `scip_solver.py`
- `SCIPSolver`: Classe para resolver o problema com SCIP
- `is_scip_available()`: Verifica disponibilidade do SCIP

### `src/cflp/utils/output.py`
Utilitários para visualização:
- `print_solution()`: Exibe resumo formatado da solução

## Uso

### Executar o modelo principal

```bash
python cflp_cantinas.py
```

### Calcular demanda total

```bash
python calculate_total_demand.py
```

### Marcar pontos no mapa

```bash
python map_point_marker.py
```

## Instalação

### Dependências

```bash
pip install -r requirements.txt
```

### Solvers (pelo menos um é necessário)

**Gurobi:**
```bash
pip install gurobipy
```

**SCIP:**
```bash
pip install pyscipopt
```

## Características

- ✅ Código modular e bem organizado
- ✅ Type hints em todas as funções
- ✅ Docstrings seguindo PEP 257
- ✅ Suporte a múltiplos solvers (Gurobi e SCIP)
- ✅ Tratamento robusto de erros
- ✅ Logging para rastreamento
- ✅ Fácil extensão e manutenção

## Documentação

Para mais detalhes sobre a implementação, consulte o arquivo `RELATORIO_CFLP.md`.

