"""Calculate Total Demand from Map Points.

This module reads the map points JSON file and calculates the total demand
of all numeric points in the map.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
JSON_PATH = Path("map_points.json")


def load_points(json_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load points from JSON file.

    Args:
        json_path: Path to the JSON file containing map points.

    Returns:
        Dictionary containing numeric_points and alpha_points arrays.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the JSON file is invalid.
    """
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    logger.info(f"Loaded points from {json_path}")
    return data


def calculate_total_demand(points_data: Dict[str, List[Dict[str, Any]]]) -> float:
    """Calculate the total demand from all numeric points.

    Args:
        points_data: Dictionary containing numeric_points and alpha_points arrays.

    Returns:
        Total demand as a float. Returns 0.0 if no points have demand values.
    """
    numeric_points = points_data.get("numeric_points", [])
    total_demand = 0.0
    points_with_demand = 0
    points_without_demand = 0

    for point in numeric_points:
        if "demand" in point:
            try:
                demand = float(point["demand"])
                total_demand += demand
                points_with_demand += 1
                logger.debug(
                    f"Point {point.get('id', 'unknown')}: demand = {demand}",
                )
            except (ValueError, TypeError) as e:
                logger.warning(
                    f"Invalid demand value for point {point.get('id', 'unknown')}: {e}",
                )
                points_without_demand += 1
        else:
            points_without_demand += 1
            logger.debug(
                f"Point {point.get('id', 'unknown')} has no demand field",
            )

    logger.info(
        f"Calculated total demand: {total_demand:.2f} "
        f"from {points_with_demand} points "
        f"({points_without_demand} points without demand)",
    )

    return total_demand


def print_summary(points_data: Dict[str, List[Dict[str, Any]]], total_demand: float) -> None:
    """Print a summary of the demand calculation.

    Args:
        points_data: Dictionary containing numeric_points and alpha_points arrays.
        total_demand: Total demand value to display.
    """
    numeric_points = points_data.get("numeric_points", [])
    alpha_points = points_data.get("alpha_points", [])

    print("\n" + "=" * 60)
    print("RESUMO DA DEMANDA DOS PONTOS DO MAPA")
    print("=" * 60)
    print(f"Total de pontos numéricos: {len(numeric_points)}")
    print(f"Total de pontos alfanuméricos: {len(alpha_points)}")
    print(f"Total de pontos: {len(numeric_points) + len(alpha_points)}")
    print("-" * 60)
    print(f"DEMANDA TOTAL: {total_demand:.2f}")
    print("=" * 60 + "\n")


def main() -> None:
    """Main entry point for calculating total demand."""
    try:
        # Load points from JSON
        points_data = load_points(JSON_PATH)

        # Calculate total demand
        total_demand = calculate_total_demand(points_data)

        # Print summary
        print_summary(points_data, total_demand)

    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        print(f"\nErro: Arquivo não encontrado: {e}\n")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {e}")
        print(f"\nErro: Arquivo JSON inválido: {e}\n")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nErro inesperado: {e}\n")


if __name__ == "__main__":
    main()

