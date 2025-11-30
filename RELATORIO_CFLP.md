# Relatório de Implementação: Problema CFLP para Otimização de Cantinas em Campus Universitário

## 1. Introdução

Este documento apresenta a implementação completa de um problema de **Capacitated Facility Location Problem (CFLP)** aplicado à otimização da construção de cantinas em um campus universitário. O objetivo é determinar onde e quais tipos de cantinas devem ser construídas para atender toda a demanda do campus, minimizando os custos totais (fixos e variáveis).

## 2. Descrição do Problema

### 2.1 Contexto

O problema consiste em:

- **Pontos de demanda**: 58 pontos numéricos no mapa, cada um com uma demanda específica (total: 4.822 unidades)
- **Pontos de instalação**: 21 pontos alfanuméricos (C1 a C21) onde cantinas podem ser construídas
- **Tipos de cantinas**: 3 tipos disponíveis (pequena, média, grande) com capacidades e custos diferentes

### 2.2 Objetivos

1. **Atender toda a demanda**: Todos os 58 pontos de demanda devem ser completamente atendidos
2. **Minimizar custos totais**: Reduzir a soma de custos fixos (construção) e variáveis (distância)
3. **Respeitar capacidades**: Cada cantina tem uma capacidade máxima de atendimento

### 2.3 Dados do Problema

#### Pontos de Demanda

- **Quantidade**: 58 pontos
- **Demanda total**: 4.822 unidades
- **Localização**: Coordenadas (x, y) no mapa
- **Formato**: Armazenados em `numeric_points` no arquivo JSON

#### Pontos de Instalação

- **Quantidade**: 21 pontos
- **Identificadores**: C1, C2, ..., C21
- **Localização**: Coordenadas (x, y) no mapa
- **Formato**: Armazenados em `alpha_points` no arquivo JSON

#### Tipos de Cantinas

| Tipo    | Capacidade   | Custo Fixo    |
| ------- | ------------ | ------------- |
| Pequena | 370 unidades | R$ 90.000,00  |
| Média   | 550 unidades | R$ 110.000,00 |
| Grande  | 700 unidades | R$ 140.000,00 |

#### Custo Variável

- **Fator de custo por distância**: 1,0 unidades monetárias por unidade de distância
- **Cálculo**: `custo_variável = distância × fator × demanda_atendida`

## 3. Modelagem Matemática

### 3.1 Conjuntos e Índices

- **I**: Conjunto de pontos de demanda (i = 1, 2, ..., 58)
- **J**: Conjunto de pontos de instalação (j = 1, 2, ..., 21)
- **K**: Conjunto de tipos de cantinas (k ∈ {pequena, média, grande})

### 3.2 Parâmetros

- **dᵢ**: Demanda no ponto i
- **fⱼₖ**: Custo fixo de construir uma cantina do tipo k no local j
- **Qₖ**: Capacidade máxima de uma cantina do tipo k
- **cᵢⱼ**: Custo variável por unidade de demanda do ponto i ao local j
  - `cᵢⱼ = distância(i, j) × 1,0`

### 3.3 Variáveis de Decisão

- **yⱼₖ**: Variável binária

  - `yⱼₖ = 1` se uma cantina do tipo k é construída no local j
  - `yⱼₖ = 0` caso contrário

- **xᵢⱼ**: Variável contínua [0, 1]
  - Fração da demanda do ponto i atendida pela cantina no local j

### 3.4 Função Objetivo

Minimizar o custo total:

```
minimize: Σⱼ Σₖ fⱼₖ × yⱼₖ + Σᵢ Σⱼ cᵢⱼ × dᵢ × xᵢⱼ
```

Onde:

- Primeiro termo: Soma dos custos fixos de todas as cantinas construídas
- Segundo termo: Soma dos custos variáveis (distância × demanda atendida)

### 3.5 Restrições

#### 3.5.1 Satisfação de Demanda

Toda demanda deve ser atendida:

```
Σⱼ xᵢⱼ = 1,  ∀i ∈ I
```

#### 3.5.2 Restrição de Capacidade

A demanda total atendida por uma cantina não pode exceder sua capacidade:

```
Σᵢ dᵢ × xᵢⱼ ≤ Σₖ Qₖ × yⱼₖ,  ∀j ∈ J
```

#### 3.5.3 Um Tipo por Local

No máximo um tipo de cantina pode ser construído em cada local:

```
Σₖ yⱼₖ ≤ 1,  ∀j ∈ J
```

#### 3.5.4 Atribuição Apenas a Instalações Abertas

Demanda só pode ser atribuída a locais com cantinas construídas:

```
xᵢⱼ ≤ Σₖ yⱼₖ,  ∀i ∈ I, ∀j ∈ J
```

#### 3.5.5 Domínio das Variáveis

```
yⱼₖ ∈ {0, 1},  ∀j ∈ J, ∀k ∈ K
0 ≤ xᵢⱼ ≤ 1,  ∀i ∈ I, ∀j ∈ J
```

## 4. Estrutura de Dados

### 4.1 Arquivo JSON (`map_points.json`)

O arquivo JSON contém a estrutura:

```json
{
  "numeric_points": [
    {
      "id": "1",
      "type": "numeric",
      "x": 725,
      "y": 539,
      "demand": 50.0
    },
    ...
  ],
  "alpha_points": [
    {
      "id": "C1",
      "type": "alphanumeric",
      "x": 1316,
      "y": 2677
    },
    ...
  ]
}
```

### 4.2 Estrutura de Dados no Código

#### Pontos de Demanda

```python
demand_points: List[Dict[str, Any]]
# Cada elemento contém: id, type, x, y, demand
```

#### Pontos de Instalação

```python
facility_points: List[Dict[str, Any]]
# Cada elemento contém: id, type, x, y
```

#### Matriz de Distâncias

```python
distance_matrix: List[List[float]]
# distance_matrix[i][j] = distância euclidiana entre ponto i e local j
```

## 5. Implementação Detalhada

### 5.1 Arquitetura do Código

O código está organizado no arquivo `cflp_cantinas.py` com as seguintes funções principais:

#### 5.1.1 Carregamento de Dados

**Função**: `load_points(json_path: Path)`

- **Responsabilidade**: Carrega pontos de demanda e instalação do arquivo JSON
- **Retorno**: Tupla `(demand_points, facility_points)`
- **Tratamento de erros**: Valida existência do arquivo e formato JSON

#### 5.1.2 Cálculo de Distâncias

**Função**: `calculate_euclidean_distance(x1, y1, x2, y2)`

- **Fórmula**: `√[(x₁ - x₂)² + (y₁ - y₂)²]`
- **Uso**: Calcula distância euclidiana entre dois pontos

**Função**: `calculate_distance_matrix(demand_points, facility_points)`

- **Responsabilidade**: Cria matriz de distâncias entre todos os pares (demanda, instalação)
- **Dimensão**: 58 × 21 = 1.218 distâncias calculadas

### 5.2 Modelagem com Gurobi

**Função**: `solve_with_gurobi(demand_points, facility_points, distance_matrix)`

#### Estrutura do Modelo

1. **Criação do modelo**:

   ```python
   model = gp.Model("CFLP_Cantinas")
   model.setParam("OutputFlag", 0)  # Suprime saída do Gurobi
   ```

2. **Definição de variáveis**:

   - `y[j, k]`: Binária, indica se cantina tipo k no local j
   - `x[i, j]`: Contínua [0,1], fração de demanda i atendida por j

3. **Função objetivo**:

   ```python
   minimize: Σ f[j,k] * y[j,k] + Σ c[i,j] * d[i] * x[i,j]
   ```

4. **Restrições implementadas**:

   - Satisfação de demanda
   - Capacidade
   - Um tipo por local
   - Atribuição apenas a instalações abertas

5. **Extração da solução**:
   - Identifica cantinas abertas (y[j,k] = 1)
   - Calcula atribuições de demanda (x[i,j] > 0)
   - Computa custos fixos e variáveis

### 5.3 Modelagem com SCIP

**Função**: `solve_with_scip(demand_points, facility_points, distance_matrix)`

#### Estrutura do Modelo

1. **Criação do modelo**:

   ```python
   model = Model("CFLP_Cantinas")
   model.hideOutput()  # Suprime saída do SCIP
   ```

2. **Definição de variáveis**:

   - `y[j, k]`: Binária (tipo "B")
   - `x[i, j]`: Contínua (tipo "C") com limites [0, 1]

3. **Função objetivo e restrições**: Idênticas ao modelo Gurobi

4. **Extração da solução**:
   - Usa `model.getVal()` para obter valores das variáveis
   - Estrutura de retorno idêntica ao Gurobi

### 5.4 Visualização de Resultados

**Função**: `print_solution(solution, solver_name)`

Exibe:

- Status da solução (ótima, inviável, etc.)
- Valor da função objetivo
- Custos fixos e variáveis totais
- Lista detalhada de cantinas abertas
- Coordenadas e tipos de cada cantina

## 6. Solvers Utilizados

### 6.1 Gurobi

- **Biblioteca**: `gurobipy`
- **Instalação**: `pip install gurobipy`
- **Licença**: Requer licença acadêmica ou comercial
- **Vantagens**:
  - Alto desempenho
  - Excelente para problemas de grande escala
  - Suporte robusto a variáveis binárias e contínuas

### 6.2 SCIP

- **Biblioteca**: `pyscipopt`
- **Instalação**: `pip install pyscipopt`
- **Licença**: Open-source (ZIB Academic License)
- **Vantagens**:
  - Gratuito para uso acadêmico
  - Bom desempenho
  - Alternativa open-source ao Gurobi

### 6.3 Tratamento de Disponibilidade

O código verifica automaticamente a disponibilidade dos solvers:

```python
try:
    import gurobipy as gp
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False
```

Se um solver não estiver disponível, o código continua executando com o solver disponível e informa o usuário.

## 7. Configurações e Parâmetros

### 7.1 Tipos de Cantinas

Definidos no código:

```python
CAFETERIA_TYPES = {
    "pequena": {
        "capacity": 370.0,
        "fixed_cost": 90000.0,
    },
    "media": {
        "capacity": 550.0,
        "fixed_cost": 110000.0,
    },
    "grande": {
        "capacity": 700.0,
        "fixed_cost": 140000.0,
    },
}
```

### 7.2 Fator de Custo por Distância

```python
DISTANCE_COST_FACTOR = 1.0
```

Este valor pode ser ajustado para refletir diferentes custos de transporte/logística.

## 8. Execução do Programa

### 8.1 Pré-requisitos

1. **Python 3.8+**
2. **Pelo menos um solver instalado**:
   ```bash
   pip install gurobipy
   # ou
   pip install pyscipopt
   ```

### 8.2 Execução

```bash
python cflp_cantinas.py
```

### 8.3 Saída Esperada

O programa:

1. Carrega os dados do arquivo `map_points.json`
2. Calcula a matriz de distâncias
3. Resolve o problema com cada solver disponível
4. Exibe os resultados formatados

### 8.4 Resultados da Execução

#### 8.4.1 Métricas dos Solvers

| Solver     | Status     | Objetivo     | Tempo (s) | Gap (%) | Cantinas |
| ---------- | ---------- | ------------ | --------- | ------- | -------- |
| Gurobi     | Ótima      | 1.797.081,09 | 0,114     | 0,0000  | 8        |
| SCIP       | Ótima      | 1.797.081,09 | 1,607     | 0,0000  | 8        |
| Heurística | Heurística | 2.650.263,61 | 0,001     | N/A     | 9        |

#### 8.4.2 Análise Comparativa

**Desempenho:**

- **Mais rápido**: Heurística (0,001s)
- **Mais lento**: SCIP (1,607s)
- **Speedup**: 1.605,29x (heurística vs SCIP)

**Qualidade da Solução:**

- **Melhor solução**: Gurobi e SCIP (objetivo = 1.797.081,09)
- **Heurística**: 47,48% pior que a solução ótima (diferença de 853.182,52)

**Gap de Optimalidade:**

- **Gurobi**: 0% (solução ótima garantida)
- **SCIP**: 0% (solução ótima garantida)
- **Heurística**: N/A (não possui bound)

**Instalações:**

- **Solvers exatos**: 8 cantinas abertas
- **Heurística**: 9 cantinas abertas

#### 8.4.3 Solução Ótima Encontrada

A solução ótima encontrada por Gurobi e SCIP consiste em **8 cantinas**:

1. **C3** (média) - Coordenadas: (1319, 2308) - Demanda: 550,00
2. **C5** (grande) - Coordenadas: (1078, 2052) - Demanda: 681,00
3. **C8** (média) - Coordenadas: (687, 1193) - Demanda: 549,00
4. **C9** (grande) - Coordenadas: (1803, 1725) - Demanda: 700,00
5. **C10** (média) - Coordenadas: (1067, 1238) - Demanda: 550,00
6. **C16** (média) - Coordenadas: (747, 661) - Demanda: 542,00
7. **C20** (grande) - Coordenadas: (1561, 1702) - Demanda: 700,00
8. **C21** (média) - Coordenadas: (1371, 1561) - Demanda: 550,00

**Distribuição de tipos:**

- 5 cantinas médias (capacidade 550 cada)
- 3 cantinas grandes (capacidade 700 cada)
- Total de capacidade: 5.450 unidades (suficiente para 4.822 de demanda)

**Custos:**

- Custo fixo total: R$ 970.000,00
- Custo variável total: R$ 827.081,09
- **Custo total**: R$ 1.797.081,09

## 9. Análise do Problema

### 9.1 Complexidade

- **Variáveis binárias**: 21 locais × 3 tipos = 63 variáveis
- **Variáveis contínuas**: 58 demandas × 21 locais = 1.218 variáveis
- **Total de variáveis**: 1.281
- **Restrições**:
  - Satisfação de demanda: 58
  - Capacidade: 21
  - Um tipo por local: 21
  - Atribuição: 58 × 21 = 1.218
  - **Total de restrições**: 1.318

### 9.2 Características do Problema

- **Tipo**: Problema de Programação Linear Mista (MILP)
- **Convexidade**: Função objetivo e restrições são lineares
- **Tamanho**: Problema de médio porte
- **Solução**: Espera-se solução ótima em tempo razoável

### 9.3 Demanda Total vs. Capacidades

- **Demanda total**: 4.822 unidades
- **Capacidade mínima necessária**: 4.822 unidades
- **Cenários possíveis**:
  - 7 cantinas grandes: 4.900 unidades (suficiente)
  - 9 cantinas médias: 4.950 unidades (suficiente)
  - 14 cantinas pequenas: 5.180 unidades (suficiente)
  - Combinações mistas são possíveis

## 10. Extensões e Melhorias Futuras

### 10.1 Possíveis Melhorias

1. **Visualização gráfica**: Plotar mapa com cantinas e atribuições
2. **Análise de sensibilidade**: Variação de custos e capacidades
3. **Restrições adicionais**:
   - Distância máxima entre demanda e cantina
   - Número mínimo/máximo de cantinas
   - Restrições geográficas
4. **Heurísticas**: Para problemas maiores
5. **Exportação de resultados**: Salvar solução em JSON/CSV

### 10.2 Casos de Uso Alternativos

- Otimização de postos de saúde
- Localização de centros de distribuição
- Planejamento de estações de recarga
- Otimização de pontos de venda

## 11. Arquivos do Projeto

### 11.1 Arquivos Principais

1. **`cflp_cantinas.py`**: Implementação principal do modelo CFLP
2. **`map_points.json`**: Dados dos pontos de demanda e instalação
3. **`map_point_marker.py`**: Aplicação GUI para marcar pontos no mapa
4. **`requirements.txt`**: Dependências do projeto
5. **`HEURISTICA.md`**: Documentação da heurística implementada

### 11.2 Estrutura de Código

```
projeto-progmat/
├── src/
│   └── cflp/
│       ├── config.py              # Configurações
│       ├── data_loader.py          # Carregamento de dados
│       ├── distance.py             # Cálculo de distâncias
│       ├── solvers/
│       │   ├── gurobi_solver.py    # Solver Gurobi
│       │   ├── scip_solver.py      # Solver SCIP
│       │   └── heuristic_solver.py # Heurística gulosa
│       └── utils/
│           └── output.py           # Visualização e comparação
├── cflp_cantinas.py                # Ponto de entrada principal
├── map_point_marker.py             # Interface gráfica
├── map_points.json                 # Dados dos pontos
├── requirements.txt                 # Dependências
├── HEURISTICA.md                   # Documentação da heurística
└── RELATORIO_CFLP.md               # Este relatório
```

## 12. Resultados Obtidos

### 12.1 Solução Ótima

Ambos os solvers exatos (Gurobi e SCIP) encontraram a **mesma solução ótima**:

- **Valor objetivo**: R$ 1.797.081,09
- **Cantinas abertas**: 8
- **Distribuição**: 5 médias + 3 grandes
- **Capacidade total**: 5.450 unidades
- **Demanda atendida**: 4.822 unidades (100%)

### 12.2 Comparação de Solvers

#### Performance

- **Gurobi**: 0,114 segundos (mais rápido entre os exatos)
- **SCIP**: 1,607 segundos (14x mais lento que Gurobi)
- **Heurística**: 0,001 segundos (extremamente rápida)

#### Qualidade

- **Gurobi e SCIP**: Solução ótima garantida (gap = 0%)
- **Heurística**: Solução 47,48% pior que a ótima

#### Observações

1. **Gurobi e SCIP** encontraram a mesma solução ótima, validando a correção da implementação
2. **Heurística** é muito rápida mas produz solução subótima significativa
3. A heurística abriu **9 cantinas** vs **8 cantinas** da solução ótima, indicando subutilização

### 12.3 Análise da Solução

A solução ótima mostra uma estratégia eficiente:

- Uso de **cantinas grandes** (700 unidades) para áreas de alta demanda concentrada
- Uso de **cantinas médias** (550 unidades) para distribuição mais ampla
- **Nenhuma cantina pequena** foi escolhida (não é economicamente viável)
- **Capacidade total** (5.450) excede demanda (4.822) em apenas 13%, indicando eficiência

## 13. Conclusões

### 13.1 Implementação Bem-Sucedida

A implementação do problema CFLP foi concluída com sucesso, incluindo:

✅ Modelagem matemática completa e correta  
✅ Implementação com dois solvers exatos (Gurobi e SCIP)  
✅ Implementação de heurística gulosa  
✅ Código bem estruturado e modularizado  
✅ Tratamento robusto de erros  
✅ Visualização clara dos resultados com métricas detalhadas  
✅ Comparação automática entre solvers

### 13.2 Características Técnicas

- **Type hints** em todas as funções
- **Docstrings** seguindo PEP 257
- **Logging** para rastreamento
- **Modularidade** e reutilização de código
- **Compatibilidade** com múltiplos solvers
- **Métricas detalhadas**: status, tempo, gap de optimalidade
- **Comparação automática** entre solvers

### 13.3 Resultados Obtidos

O modelo encontrou uma solução ótima que:

✅ Atende toda a demanda (4.822 unidades)  
✅ Minimiza custos totais (R$ 1.797.081,09)  
✅ Respeita capacidades das cantinas  
✅ Determina localizações e tipos ideais (8 cantinas: 5 médias + 3 grandes)

### 13.4 Aplicabilidade

A solução desenvolvida pode ser aplicada a:

- Problemas reais de localização de facilidades
- Planejamento urbano e campus universitários
- Otimização logística
- Problemas de alocação de recursos

---

## Referências

- **Gurobi Optimization**: https://www.gurobi.com/
- **SCIP Optimization Suite**: https://www.scipopt.org/
- **Facility Location Problems**: Daskin, M.S. (2008). "What You Should Know About Location Modeling"

---

**Data de Criação**: 2025-11-30  
**Última Atualização**: 2025-11-30  
**Versão**: 2.0  
**Autor**: Implementação para projeto de programação matemática
