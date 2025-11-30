"""
Carregamento de dados do problema.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def load_points(json_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Carrega os pontos do arquivo JSON.

    O arquivo deve ter a estrutura:
    {
        "numeric_points": [...],  # pontos com demanda
        "alpha_points": [...]      # locais possíveis para cantinas
    }

    """
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    # Lê o arquivo com encoding UTF-8 para suportar caracteres especiais
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extrai os dois tipos de pontos
    # Usa get() com lista vazia como default para evitar KeyError
    demand_points = data.get("numeric_points", [])
    facility_points = data.get("alpha_points", [])

    logger.info(
        f"Loaded {len(demand_points)} demand points and "
        f"{len(facility_points)} facility location points",
    )

    return demand_points, facility_points

