"""Distance calculation module for CFLP problem.

This module provides functions for calculating distances between points
and building distance matrices.
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
    """Calculate Euclidean distance between two points.

    Args:
        x1: X coordinate of first point.
        y1: Y coordinate of first point.
        x2: X coordinate of second point.
        y2: Y coordinate of second point.

    Returns:
        Euclidean distance between the two points.
    """
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def calculate_distance_matrix(
    demand_points: List[Dict[str, Any]],
    facility_points: List[Dict[str, Any]],
) -> List[List[float]]:
    """Calculate distance matrix between demand points and facility locations.

    Args:
        demand_points: List of demand point dictionaries with x, y coordinates.
        facility_points: List of facility location dictionaries with x, y coordinates.

    Returns:
        Matrix where distance_matrix[i][j] is the distance from demand point i
        to facility location j.
    """
    distance_matrix: List[List[float]] = []

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

