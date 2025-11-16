# src/exercise_progression/infrastructure/routes/exercise_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging
import uuid

from src.exercise_progression.infrastructure.controllers.exercise_controller import ExerciseController
from src.exercise_progression.infrastructure.helpers.dependencies import get_exercise_controller
from src.shared.auth_dependency import get_current_user

logger = logging.getLogger(__name__)
# Router
exercise_router = APIRouter(
    prefix="/exercises",
    tags=["Exercise Progression"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Sin permiso para acceder"},
        404: {"description": "Ejercicio no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)


# ============================================
# RUTAS ESPECÍFICAS PRIMERO (antes de /{exercise_id})
# ============================================

@exercise_router.get(
    "/map",  # ← Ruta específica PRIMERO
    summary="Obtener mapa de ejercicios",
    description="""
    Obtiene el mapa completo de ejercicios con sus estados para el usuario actual.
    
    Retorna:
    - Lista de ejercicios agrupados por categoría (Fonemas, Ritmo, Entonación)
    - Estado de cada ejercicio (locked, available, in_progress, completed, mastered)
    - Progreso del usuario (best_score, stars, attempts)
    - Estadísticas generales (total completados, total estrellas, % completado)
    """,
    response_description="Mapa completo de ejercicios con estados",
    status_code=200
)
@exercise_router.get("/map")
async def get_exercise_map(
    current_user: dict = Depends(get_current_user),
    controller: ExerciseController = Depends(get_exercise_controller)
) -> Dict:
    """Endpoint: Obtener mapa de ejercicios."""    
    user_id = uuid.UUID(current_user["user_id"])
    
    result = await controller.get_exercise_map(user_id)
    
    return result

@exercise_router.get(
    "/stats/summary",  # ← Ruta específica PRIMERO
    summary="Obtener estadísticas del usuario",
    description="""
    Obtiene estadísticas generales del progreso del usuario.
    
    Incluye:
    - Total de ejercicios completados
    - Total de estrellas obtenidas
    - Porcentaje de completado
    - Desglose por categoría
    """,
    response_description="Estadísticas del usuario",
    status_code=200
)
async def get_user_stats(
    current_user: dict = Depends(get_current_user),
    controller: ExerciseController = Depends(get_exercise_controller)
) -> Dict:
    """
    Endpoint: Obtener estadísticas.
    """
    user_id = uuid.UUID(current_user["user_id"])
    map_data = await controller.get_exercise_map(user_id)
    
    # Extraer solo las estadísticas
    return {
        "total_exercises": map_data["total_exercises"],
        "completed_count": map_data["completed_count"],
        "total_stars": map_data["total_stars"],
        "max_stars": map_data["max_stars"],
        "completion_percentage": map_data["completion_percentage"],
        "by_category": {
            cat["category"]: {
                "total": cat["total"],
                "completed": cat["completed"],
                "stars": cat["total_stars"]
            }
            for cat in map_data["categories"]
        }
    }


# ============================================
# RUTAS CON PARÁMETROS DINÁMICOS AL FINAL
# ============================================

@exercise_router.get(
    "/{exercise_id}",  # ← Ruta dinámica AL FINAL
    summary="Obtener detalles de ejercicio",
    description="""
    Obtiene información detallada de un ejercicio específico.
    
    Incluye:
    - Información del ejercicio (título, categoría, texto, dificultad)
    - Progreso del usuario en ese ejercicio
    - Tips y recomendaciones
    - URL del audio de referencia
    """,
    response_description="Detalles del ejercicio",
    status_code=200
)
async def get_exercise_details(
    exercise_id: str,
    current_user: dict = Depends(get_current_user),
    controller: ExerciseController = Depends(get_exercise_controller)
) -> Dict:
    """
    Endpoint: Obtener detalles de un ejercicio.
    """
    user_id = uuid.UUID(current_user["user_id"])
    result = await controller.get_exercise_details(user_id, exercise_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejercicio '{exercise_id}' no encontrado"
        )
    
    return result
# src/exercise_progression/infrastructure/routes/exercise_routes.py

@exercise_router.post(
    "/initialize-progress",
    summary="Inicializar progreso de usuario",
    description="""
    Inicializa el progreso para un usuario nuevo.
    
    Crea registros en user_exercise_progress:
    - Primer ejercicio (order_index=1): status = 'available'
    - Resto de ejercicios: status = 'locked'
    
    Este endpoint debe llamarse cuando un usuario nuevo se registra.
    """,
    status_code=200
)
async def initialize_user_progress(
    current_user: dict = Depends(get_current_user)
):
    """
    Endpoint: Inicializar progreso del usuario.
    
    Args:
        current_user: Usuario autenticado (del JWT)
    
    Returns:
        Confirmación de inicialización
    """
    from src.exercise_progression.infrastructure.helpers.dependencies import (
        get_progress_repository
    )
    
    user_id = uuid.UUID(current_user["user_id"])
    progress_repo = get_progress_repository()
    
    try:
        # Inicializar progreso
        await progress_repo.initialize_user_progress(user_id)
        
        # Verificar cuántos ejercicios se crearon
        from src.exercise_progression.infrastructure.helpers.dependencies import (
            get_exercise_repository
        )
        exercise_repo = get_exercise_repository()
        total_exercises = await exercise_repo.count_total()
        
        return {
            "success": True,
            "data": {
                "user_id": str(user_id),
                "total_exercises_initialized": total_exercises,
                "first_exercise_unlocked": True,
                "message": "Progreso inicializado correctamente. Puedes empezar con el primer ejercicio."
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error inicializando progreso: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al inicializar progreso: {str(e)}"
        )