"""
Exercise Routes - Definiciones de rutas FastAPI para ejercicios.

Define los endpoints HTTP y conecta con los controladores.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from src.exercises.infrastructure.controllers.exercise_controller import (
    ExerciseController,
    ExerciseHealthController
)
from src.exercises.infrastructure.helpers.dependencies import (
    get_exercise_controller,
    get_health_controller
)


# Router para ejercicios
exercises_router = APIRouter(
    prefix="/exercises",
    tags=["exercises"]
)


@exercises_router.get(
    "",
    response_model=dict,
    summary="Obtener lista de ejercicios",
    description="Obtiene una lista paginada de ejercicios con filtros opcionales"
)
async def get_exercises(
    category: Optional[str] = Query(
        None,
        description="Filtrar por categoría: fonema, ritmo, entonacion"
    ),
    subcategory: Optional[str] = Query(
        None,
        description="Filtrar por subcategoría específica"
    ),
    difficulty_level: Optional[int] = Query(
        None,
        ge=1,
        le=5,
        description="Filtrar por nivel de dificultad (1-5)"
    ),
    is_active: bool = Query(
        True,
        description="Filtrar ejercicios activos/inactivos"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Número máximo de resultados"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Offset para paginación"
    ),
    controller: ExerciseController = Depends(get_exercise_controller)
):
    """
    Obtiene una lista paginada de ejercicios.
    
    **Filtros disponibles:**
    - category: fonema, ritmo, entonacion
    - subcategory: r_suave, r_fuerte, pregunta, etc.
    - difficulty_level: 1 (muy fácil) a 5 (muy difícil)
    - is_active: true/false
    
    **Paginación:**
    - limit: máximo 100 resultados por página
    - offset: desplazamiento para paginación
    
    **Respuesta:**
    ```json
    {
        "exercises": [...],
        "total": 45,
        "limit": 50,
        "offset": 0
    }
    ```
    """
    return await controller.get_exercises(
        category=category,
        subcategory=subcategory,
        difficulty_level=difficulty_level,
        is_active=is_active,
        limit=limit,
        offset=offset
    )


@exercises_router.get(
    "/{exercise_id}",
    response_model=dict,
    summary="Obtener ejercicio por ID",
    description="Obtiene un ejercicio específico por su ID (UUID o exercise_id)"
)
async def get_exercise_by_id(
    exercise_id: str,
    controller: ExerciseController = Depends(get_exercise_controller)
):
    """
    Obtiene un ejercicio específico.
    
    **Parámetros:**
    - exercise_id: UUID o exercise_id (ej: "fonema_r_suave_1")
    
    **Respuesta:**
    ```json
    {
        "found": true,
        "exercise": {
            "id": "...",
            "exercise_id": "fonema_r_suave_1",
            "category": "fonema",
            "subcategory": "r_suave",
            "text_content": "raro",
            "difficulty_level": 2,
            ...
        }
    }
    ```
    """
    return await controller.get_exercise_by_id(exercise_id)


@exercises_router.get(
    "/{exercise_id}/details",
    response_model=dict,
    summary="Obtener detalles completos del ejercicio",
    description="Obtiene detalles completos incluyendo ejercicios relacionados y metadata"
)
async def get_exercise_details(
    exercise_id: str,
    controller: ExerciseController = Depends(get_exercise_controller)
):
    """
    Obtiene detalles completos de un ejercicio.
    
    Incluye:
    - Datos completos del ejercicio
    - Ejercicios relacionados (misma subcategoría)
    - Rango de duración esperada
    - Metadata adicional
    
    **Respuesta:**
    ```json
    {
        "id": "...",
        "exercise_id": "fonema_r_suave_1",
        ...
        "related_exercises": [...],
        "expected_duration_range": [0.5, 2.0],
        "metadata": {
            "is_phoneme_exercise": true,
            "has_target_phonemes": true,
            ...
        }
    }
    ```
    """
    return await controller.get_exercise_details(exercise_id)


@exercises_router.get(
    "/{exercise_id}/reference-features",
    response_model=dict,
    summary="Obtener features de referencia",
    description="Obtiene las features precalculadas del audio de referencia"
)
async def get_reference_features(
    exercise_id: str,
    controller: ExerciseController = Depends(get_exercise_controller)
):
    """
    Obtiene features precalculadas del audio de referencia.
    
    Incluye:
    - Estadísticas de MFCCs
    - Estadísticas prosódicas (F0, jitter, shimmer)
    - Segmentos fonéticos
    - Parámetros de normalización
    - Umbrales de comparación
    
    **Respuesta:**
    ```json
    {
        "found": true,
        "exercise_exists": true,
        "features": {
            "exercise_id": "fonema_r_suave_1",
            "mfcc_stats": {...},
            "prosody_stats": {...},
            "phoneme_segments": [...],
            "duration_seconds": 1.5,
            ...
        }
    }
    ```
    """
    return await controller.get_reference_features(exercise_id)


@exercises_router.get(
    "/{exercise_id}/features-comparison",
    response_model=dict,
    summary="Obtener features optimizadas para comparación",
    description="Obtiene solo las features necesarias para comparación DTW (payload reducido)"
)
async def get_features_for_comparison(
    exercise_id: str,
    controller: ExerciseController = Depends(get_exercise_controller)
):
    """
    Obtiene features optimizadas para comparación DTW.
    
    Retorna un payload reducido con solo las features esenciales:
    - Estadísticas de MFCCs (mean, std)
    - Estadísticas prosódicas básicas
    - Parámetros de normalización
    - Umbrales de comparación
    
    Este endpoint es más rápido y usa menos ancho de banda que
    el endpoint completo de features.
    
    **Respuesta:**
    ```json
    {
        "exercise_id": "fonema_r_suave_1",
        "mfcc_stats": {
            "mean": [...],
            "std": [...]
        },
        "prosody_stats": {
            "f0_mean": 120.5,
            "f0_std": 15.2,
            "f0_range": 80.0
        },
        "duration_seconds": 1.5,
        "normalization_params": {...},
        "thresholds": {...}
    }
    ```
    """
    return await controller.get_features_for_comparison(exercise_id)


# Router para health y monitoreo
health_router = APIRouter(
    prefix="/exercises",
    tags=["exercises-health"]
)


@health_router.get(
    "/health",
    response_model=dict,
    summary="Health check del módulo de ejercicios",
    description="Verifica el estado del módulo de ejercicios"
)
async def health_check(
    controller: ExerciseHealthController = Depends(get_health_controller)
):
    """
    Verifica el estado de salud del módulo de ejercicios.
    
    **Respuesta:**
    ```json
    {
        "status": "healthy",
        "exercises_count": 45,
        "cached_features_count": 42,
        "cache_coverage": "93.3%"
    }
    ```
    """
    return await controller.health_check()


@health_router.get(
    "/statistics",
    response_model=dict,
    summary="Estadísticas del módulo de ejercicios",
    description="Obtiene estadísticas detalladas del módulo"
)
async def get_statistics(
    controller: ExerciseHealthController = Depends(get_health_controller)
):
    """
    Obtiene estadísticas del módulo de ejercicios.
    
    **Respuesta:**
    ```json
    {
        "total_exercises": 45,
        "exercises_by_category": {
            "fonema": 20,
            "ritmo": 15,
            "entonacion": 10
        },
        "cached_features": 42,
        "cache_coverage_percentage": 93.33
    }
    ```
    """
    return await controller.get_statistics()


# Exportar routers
__all__ = [
    "exercises_router",
    "health_router"
]

