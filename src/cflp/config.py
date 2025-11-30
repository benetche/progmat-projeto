"""
Configurações do problema CFLP.
"""

from pathlib import Path
from typing import Dict

# Arquivo JSON com os pontos do mapa
JSON_PATH = Path("map_points.json")

# Tipos de cantinas disponíveis com suas características
# Valores atualizados conforme especificação do problema
CAFETERIA_TYPES: Dict[str, Dict[str, float]] = {
    "pequena": {
        "capacity": 370.0,  # unidades de demanda
        "fixed_cost": 90000.0,  # R$
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

# Fator de custo por distância - multiplica a distância pela demanda
# para calcular o custo variável de transporte
DISTANCE_COST_FACTOR = 1.0

