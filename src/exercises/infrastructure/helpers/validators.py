"""
Validators - Utilidades de validación para la capa de infraestructura.

Proporciona validadores específicos para requests HTTP.
"""

import re
from typing import Optional
from fastapi import HTTPException, status


def validate_exercise_id_format(exercise_id: str) -> str:
    """
    Valida el formato de un exercise_id.
    
    Formato esperado: categoria_subcategoria_numero
    Ejemplo: fonema_r_suave_1
    
    Args:
        exercise_id: ID a validar
    
    Returns:
        str: exercise_id validado (stripped)
    
    Raises:
        HTTPException: Si el formato es inválido
    """
    if not exercise_id or not exercise_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El exercise_id no puede estar vacío"
        )
    
    exercise_id = exercise_id.strip()
    
    # Validar formato básico con regex
    # Permite: letras minúsculas, números y guiones bajos
    pattern = r'^[a-z0-9_]+$'
    if not re.match(pattern, exercise_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El exercise_id solo puede contener letras minúsculas, números y guiones bajos"
        )
    
    # Verificar que tenga al menos 3 partes separadas por _
    parts = exercise_id.split('_')
    if len(parts) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El exercise_id debe tener formato: categoria_subcategoria_numero"
        )
    
    return exercise_id


def validate_category(category: Optional[str]) -> Optional[str]:
    """
    Valida que la categoría sea válida.
    
    Args:
        category: Categoría a validar
    
    Returns:
        Optional[str]: Categoría validada o None
    
    Raises:
        HTTPException: Si la categoría es inválida
    """
    if not category:
        return None
    
    valid_categories = ["fonema", "ritmo", "entonacion"]
    
    if category.lower() not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoría inválida. Valores permitidos: {', '.join(valid_categories)}"
        )
    
    return category.lower()


def validate_difficulty_level(difficulty: Optional[int]) -> Optional[int]:
    """
    Valida el nivel de dificultad.
    
    Args:
        difficulty: Nivel de dificultad (1-5)
    
    Returns:
        Optional[int]: Nivel validado o None
    
    Raises:
        HTTPException: Si el nivel es inválido
    """
    if difficulty is None:
        return None
    
    if difficulty < 1 or difficulty > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nivel de dificultad debe estar entre 1 y 5"
        )
    
    return difficulty


def validate_pagination_params(limit: int, offset: int) -> tuple[int, int]:
    """
    Valida parámetros de paginación.
    
    Args:
        limit: Límite de resultados
        offset: Offset para paginación
    
    Returns:
        tuple[int, int]: (limit, offset) validados
    
    Raises:
        HTTPException: Si los parámetros son inválidos
    """
    if limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El límite debe ser mayor a 0"
        )
    
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El límite máximo es 100"
        )
    
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El offset no puede ser negativo"
        )
    
    return limit, offset


def validate_uuid_format(uuid_str: str) -> bool:
    """
    Valida si un string tiene formato UUID.
    
    Args:
        uuid_str: String a validar
    
    Returns:
        bool: True si es un UUID válido
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_str))

