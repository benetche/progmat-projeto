"""
Cálculo de distâncias entre pontos.

"""

import logging
import math
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def calculate_euclidean_distance(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> float:

    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def calculate_distance_matrix(
    demand_points: List[Dict[str, Any]],
    facility_points: List[Dict[str, Any]],
) -> List[List[float]]:

    distance_matrix: List[List[float]] = []

    # Para cada ponto de demanda, calcula distância para todas as instalações
    for demand_point in demand_points:
        row: List[float] = []
        for facility_point in facility_points:
            distance = calculate_euclidean_distance(
                demand_point["x"],
                demand_point["y"],
                facility_point["x"],
                facility_point["y"],
            )
            row.append(distance)
        distance_matrix.append(row)

    logger.info("Calculated distance matrix")
    return distance_matrix

