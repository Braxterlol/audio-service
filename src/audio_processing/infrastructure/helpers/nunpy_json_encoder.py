"""
JSON Encoder Helper - Convierte tipos numpy a tipos Python nativos.

Útil para serializar respuestas con numpy arrays/scalars a JSON.
"""

import numpy as np
from typing import Any


def convert_numpy_types(obj: Any) -> Any:
    """
    Convierte tipos numpy a tipos Python nativos recursivamente.
    
    Args:
        obj: Objeto a convertir (puede ser dict, list, numpy array, etc.)
    
    Returns:
        Objeto con tipos Python nativos
    """
    # Numpy scalars
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    
    if isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    
    if isinstance(obj, np.bool_):
        return bool(obj)
    
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    
    # Diccionarios
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    
    # Listas y tuplas
    if isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    
    # Otros tipos (str, int, float, bool, None)
    return obj


def safe_float(value: Any) -> float:
    """Convierte un valor a float de forma segura."""
    if value is None:
        return None
    if isinstance(value, (np.floating, np.integer, np.bool_)):
        return float(value)
    return float(value)


def safe_bool(value: Any) -> bool:
    """Convierte un valor a bool de forma segura."""
    if value is None:
        return None
    if isinstance(value, np.bool_):
        return bool(value)
    return bool(value)


def safe_int(value: Any) -> int:
    """Convierte un valor a int de forma segura."""
    if value is None:
        return None
    if isinstance(value, (np.integer, np.bool_)):
        return int(value)
    return int(value)