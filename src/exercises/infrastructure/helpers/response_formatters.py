"""
Response Formatters - Utilidades para formatear respuestas HTTP.

Proporciona funciones helper para formatear respuestas consistentes.
"""

from typing import Any, Optional
from datetime import datetime


def success_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200
) -> dict:
    """
    Formatea una respuesta exitosa estándar.
    
    Args:
        data: Datos de la respuesta
        message: Mensaje opcional
        status_code: Código de estado HTTP
    
    Returns:
        dict: Respuesta formateada
    """
    response = {
        "success": True,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if message:
        response["message"] = message
    
    return response


def error_response(
    error: str,
    details: Optional[Any] = None,
    status_code: int = 500
) -> dict:
    """
    Formatea una respuesta de error estándar.
    
    Args:
        error: Mensaje de error
        details: Detalles adicionales del error
        status_code: Código de estado HTTP
    
    Returns:
        dict: Respuesta formateada
    """
    response = {
        "success": False,
        "error": error,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if details:
        response["details"] = details
    
    return response


def paginated_response(
    items: list,
    total: int,
    limit: int,
    offset: int,
    message: Optional[str] = None
) -> dict:
    """
    Formatea una respuesta paginada estándar.
    
    Args:
        items: Lista de items
        total: Total de items disponibles
        limit: Límite de items por página
        offset: Offset actual
        message: Mensaje opcional
    
    Returns:
        dict: Respuesta paginada formateada
    """
    response = {
        "success": True,
        "data": items,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "count": len(items),
            "has_more": (offset + len(items)) < total
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if message:
        response["message"] = message
    
    return response


def not_found_response(
    resource: str,
    resource_id: str
) -> dict:
    """
    Formatea una respuesta de recurso no encontrado.
    
    Args:
        resource: Tipo de recurso (ej: "exercise")
        resource_id: ID del recurso
    
    Returns:
        dict: Respuesta de no encontrado
    """
    return error_response(
        error=f"{resource.capitalize()} no encontrado",
        details={
            "resource": resource,
            "resource_id": resource_id
        },
        status_code=404
    )


def validation_error_response(
    field: str,
    message: str,
    value: Optional[Any] = None
) -> dict:
    """
    Formatea una respuesta de error de validación.
    
    Args:
        field: Campo que falló la validación
        message: Mensaje de error
        value: Valor que causó el error (opcional)
    
    Returns:
        dict: Respuesta de error de validación
    """
    details = {
        "field": field,
        "message": message
    }
    
    if value is not None:
        details["value"] = value
    
    return error_response(
        error="Error de validación",
        details=details,
        status_code=400
    )

