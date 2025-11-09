"""
Attempt Routes - Endpoints para historial de intentos y progreso.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path

from src.audio_processing.domain.models import attempt
from src.audio_processing.infrastructure.helpers.dependencies import (
    get_attempt_controller
)
from src.audio_processing.infrastructure.controllers.attempt_controller import (
    AttemptController
)
from src.shared.auth_dependency import get_current_user


# ============================================
# ROUTER
# ============================================

attempt_router = APIRouter(
    prefix="/attempts",
    tags=["Attempts & Progress"],
    responses={
        401: {"description": "No autenticado"},
        404: {"description": "Recurso no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)


# ============================================
# ENDPOINTS
# ============================================

@attempt_router.get(
    "",
    summary="Obtener historial de intentos",
    description="""
    Obtiene el historial de intentos del usuario autenticado.
    
    Permite filtrar por:
    - **exercise_id**: Ver intentos de un ejercicio específico
    - **status**: Filtrar por estado (completed, quality_rejected, pending_analysis)
    - **days**: Ver intentos de los últimos N días
    
    Soporta paginación con limit y offset.
    """,
    response_description="Lista de intentos con paginación",
    status_code=200
)
async def get_user_attempts(
    exercise_id: Optional[str] = Query(
        None,
        description="Filtrar por ejercicio específico",
        pattern="^[a-z0-9_]+$"
    ),
    status: Optional[str] = Query(
        None,
        description="Filtrar por estado (completed, quality_rejected, pending_analysis)"
    ),
    days: Optional[int] = Query(
        None,
        description="Últimos N días (ej: 7 para última semana)",
        ge=1,
        le=365
    ),
    limit: int = Query(
        20,
        description="Máximo de resultados por página",
        ge=1,
        le=100
    ),
    offset: int = Query(
        0,
        description="Offset para paginación",
        ge=0
    ),
    current_user: dict = Depends(get_current_user),
    controller: AttemptController = Depends(get_attempt_controller)
):
    """
    Endpoint: Obtener historial de intentos.
    
    Args:
        exercise_id: Filtrar por ejercicio
        status: Filtrar por estado
        days: Últimos N días
        limit: Límite de resultados
        offset: Offset de paginación
        current_user: Usuario autenticado
        controller: Controller
    
    Returns:
        Lista de intentos con paginación
    """
    user_id = current_user["user_id"]
    
    return await controller.get_user_attempts(
        user_id=user_id,
        exercise_id=exercise_id,
        status=status,
        days=days,
        limit=limit,
        offset=offset
    )


@attempt_router.get(
    "/{attempt_id}",
    summary="Obtener detalle de un intento",
    description="""
    Obtiene el detalle completo de un intento específico.
    
    Incluye:
    - Información básica del intento
    - Métricas de calidad del audio
    - Métricas acústicas (duration, speech_rate, etc.)
    - Scores de pronunciación (si ya fueron calculados por ML)
    - Timestamps de procesamiento
    """,
    response_description="Detalle completo del intento",
    status_code=200
)
async def get_attempt_by_id(
    attempt_id: str = Path(
        ...,
        description="UUID del intento",
        pattern="^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    ),
    current_user: dict = Depends(get_current_user),
    controller: AttemptController = Depends(get_attempt_controller)
):
    """
    Endpoint: Obtener detalle de un intento.
    
    Args:
        attempt_id: UUID del intento
        current_user: Usuario autenticado
        controller: Controller
    
    Returns:
        Detalle del intento
    """
    user_id = current_user["user_id"]
    
    return await controller.get_attempt_by_id(
        attempt_id=attempt_id,
        user_id=user_id
    )


@attempt_router.get(
    "/progress/summary",
    summary="Obtener progreso del usuario",
    description="""
    Obtiene estadísticas y progreso del usuario en un período de tiempo.
    
    Incluye:
    - **Summary**: Total de intentos, promedio de scores, tiempo de práctica
    - **Scores Evolution**: Evolución de scores a lo largo del tiempo
    - **Exercises Stats**: Estadísticas por ejercicio y categoría
    - **Activity by Day**: Actividad diaria en el período
    
    Útil para mostrar dashboard de progreso en la app.
    """,
    response_description="Progreso y estadísticas del usuario",
    status_code=200
)
async def get_user_progress(
    days: int = Query(
        30,
        description="Período de análisis (últimos N días)",
        ge=1,
        le=365
    ),
    current_user: dict = Depends(get_current_user),
    controller: AttemptController = Depends(get_attempt_controller)
):
    """
    Endpoint: Obtener progreso del usuario.
    
    Args:
        days: Período de análisis
        current_user: Usuario autenticado
        controller: Controller
    
    Returns:
        Progreso y estadísticas
    """
    user_id = current_user["user_id"]
    
    return await controller.get_user_progress(
        user_id=user_id,
        days=days
    )


@attempt_router.get(
    "/health",
    summary="Health check del módulo de attempts",
    description="Verifica que el módulo de attempts esté funcionando",
    tags=["Health"],
    status_code=200
)
async def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "module": "attempts",
        "status": "healthy"
    }