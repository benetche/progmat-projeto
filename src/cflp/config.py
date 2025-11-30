"""Configuration module for CFLP problem.

This module contains all configuration constants and parameters for the
Capacitated Facility Location Problem.
"""

from pathlib import Path
from typing import Dict

# Path to JSON file containing map points
JSON_PATH = Path("map_points.json")

# Cafeteria types configuration
CAFETERIA_TYPES: Dict[str, Dict[str, float]] = {
    "pequena": {
        "capacity": 370.0,  # Capacidade máxima de demanda atendida
        "fixed_cost": 90000.0,  # Custo fixo de construção
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

# Cost per unit distance (custo variável por unidade de distância)
DISTANCE_COST_FACTOR = 1.0

