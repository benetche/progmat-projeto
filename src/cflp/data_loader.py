"""Data loading module for CFLP problem.

This module handles loading demand points and facility location points
from JSON files.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def load_points(json_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load demand points and facility location points from JSON file.

    Args:
        json_path: Path to the JSON file containing map points.

    Returns:
        Tuple containing (demand_points, facility_points).

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the JSON file is invalid.
    """
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    demand_points = data.get("numeric_points", [])
    facility_points = data.get("alpha_points", [])

    logger.info(
        f"Loaded {len(demand_points)} demand points and "
        f"{len(facility_points)} facility location points",
    )

    return demand_points, facility_points

