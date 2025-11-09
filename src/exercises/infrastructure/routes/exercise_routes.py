"""
Exercise Routes - Definiciones de rutas FastAPI para ejercicios.

Define los endpoints HTTP y conecta con los controladores.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from src.exercises.infrastructure.controllers.exercise_controller import (
    ExerciseController,
    ExerciseHealthController
)
from src.exercises.infrastructure.helpers.dependencies import (
    get_exercise_controller,
    get_health_controller
)
from src.exercises.domain.models.exercise import ExerciseCategory
from src.shared.auth_dependency import get_current_user


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
    """Obtiene una lista paginada de ejercicios."""
    return await controller.get_exercises(
        category=category,
        subcategory=subcategory,
        difficulty_level=difficulty_level,
        is_active=is_active,
        limit=limit,
        offset=offset
    )


@exercises_router.get(
    "/available",
    summary="Obtener ejercicios disponibles según progreso del usuario",
    description="""
    Retorna los ejercicios disponibles para el usuario según su progreso.
    
    Lógica de desbloqueo:
    - Al iniciar, solo el primer ejercicio de cada categoría está desbloqueado
    - Al completar un ejercicio (score ≥ 70), se desbloquea el siguiente
    - Los ejercicios completados permanecen disponibles para reintento
    
    Estados posibles:
    - **locked**: Bloqueado, no disponible aún
    - **unlocked**: Desbloqueado, listo para intentar
    - **in_progress**: Comenzado pero no completado
    - **completed**: Completado con score aprobatorio (≥ 70)
    - **mastered**: Dominado (score ≥ 95)
    """,
    response_description="Lista de ejercicios con estado de progreso",
    status_code=200
)
async def get_available_exercises(
    category: Optional[str] = Query(
        None,
        description="Filtrar por categoría (fonemas, ritmo, entonacion)"
    ),
    include_locked: bool = Query(
        False,
        description="Incluir ejercicios bloqueados en la respuesta"
    ),
    current_user: dict = Depends(get_current_user),
    controller: ExerciseController = Depends(get_exercise_controller)
):
    """
    Endpoint: Obtener ejercicios disponibles.
    
    Args:
        category: Filtrar por categoría
        include_locked: Incluir ejercicios bloqueados
        current_user: Usuario autenticado
        controller: Controller con use cases
    
    Returns:
        Lista de ejercicios con progreso
    """
    user_id = current_user["user_id"]
    
    # Convertir category string a enum si viene
    category_enum = None
    if category:
        try:
            category_enum = ExerciseCategory(category.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Categoría inválida: {category}. Valores válidos: fonemas, ritmo, entonacion"
            )
    
    return await controller.get_available_exercises(
        user_id=user_id,
        category=category_enum,
        include_locked=include_locked
    )


@exercises_router.post(
    "/initialize-progress",
    summary="Inicializar progreso de un nuevo usuario",
    description="""
    Inicializa el progreso de un usuario desbloqueando el primer ejercicio
    de cada categoría.
    
    Este endpoint se llama automáticamente la primera vez que el usuario
    accede a /available, pero también puede llamarse manualmente si es necesario.
    """,
    status_code=200
)
async def initialize_user_progress(
    current_user: dict = Depends(get_current_user),
    controller: ExerciseController = Depends(get_exercise_controller)
):
    """
    Endpoint: Inicializar progreso del usuario.
    
    Args:
        current_user: Usuario autenticado
        controller: Controller
    
    Returns:
        Lista de ejercicios desbloqueados
    """
    user_id = current_user["user_id"]
    
    return await controller.initialize_user_progress(user_id)


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
    """Obtiene un ejercicio específico."""
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
    """Obtiene detalles completos de un ejercicio."""
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
    """Obtiene features precalculadas del audio de referencia."""
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
    """Obtiene features optimizadas para comparación DTW."""
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
    """Verifica el estado de salud del módulo de ejercicios."""
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
    """Obtiene estadísticas del módulo de ejercicios."""
    return await controller.get_statistics()


# Exportar routers
__all__ = [
    "exercises_router",
    "health_router"
]