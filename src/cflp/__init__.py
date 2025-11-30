"""CFLP Module.

Main module for the Capacitated Facility Location Problem implementation.
"""

from src.cflp.config import CAFETERIA_TYPES, DISTANCE_COST_FACTOR, JSON_PATH
from src.cflp.data_loader import load_points
from src.cflp.distance import calculate_distance_matrix, calculate_euclidean_distance
from src.cflp.utils.output import print_solution

__all__ = [
    "CAFETERIA_TYPES",
    "DISTANCE_COST_FACTOR",
    "JSON_PATH",
    "load_points",
    "calculate_distance_matrix",
    "calculate_euclidean_distance",
    "print_solution",
]

