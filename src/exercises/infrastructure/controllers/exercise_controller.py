"""
ExerciseController - Controlador para manejar requests HTTP relacionados con ejercicios.

Responsabilidades:
- Validar parámetros HTTP
- Invocar casos de uso
- Formatear respuestas HTTP
"""

from typing import Optional
from fastapi import HTTPException, status
from src.exercises.application.use_cases.get_exercises_use_case import (
    GetExercisesUseCase,
    GetExercisesRequest,
    GetExercisesResponse
)
from src.exercises.application.use_cases.get_exercise_by_id_use_case import (
    GetExerciseByIdUseCase,
    GetExerciseDetailsUseCase,
    GetExerciseByIdRequest
)
from src.exercises.application.use_cases.get_reference_features_use_case import (
    GetReferenceFeaturesUseCase,
    GetReferenceFeaturesRequest,
    GetReferenceFeaturesForComparisonUseCase
)


class ExerciseController:
    """
    Controlador de ejercicios.
    
    Actúa como adaptador entre HTTP (FastAPI) y los casos de uso.
    """
    
    def __init__(
        self,
        get_exercises_use_case: GetExercisesUseCase,
        get_exercise_by_id_use_case: GetExerciseByIdUseCase,
        get_exercise_details_use_case: GetExerciseDetailsUseCase,
        get_reference_features_use_case: GetReferenceFeaturesUseCase,
        get_features_for_comparison_use_case: GetReferenceFeaturesForComparisonUseCase
    ):
        self.get_exercises_use_case = get_exercises_use_case
        self.get_exercise_by_id_use_case = get_exercise_by_id_use_case
        self.get_exercise_details_use_case = get_exercise_details_use_case
        self.get_reference_features_use_case = get_reference_features_use_case
        self.get_features_for_comparison_use_case = get_features_for_comparison_use_case
    
    async def get_exercises(
        self,
        category: Optional[str] = None,
        subcategory: Optional[str] = None,
        difficulty_level: Optional[int] = None,
        is_active: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> dict:
        """
        Obtiene lista de ejercicios con filtros.
        
        Args:
            category: Categoría opcional
            subcategory: Subcategoría opcional
            difficulty_level: Nivel de dificultad opcional
            is_active: Filtrar activos/inactivos
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            dict: Respuesta con ejercicios y metadata
        
        Raises:
            HTTPException: Si hay errores de validación
        """
        try:
            request = GetExercisesRequest(
                category=category,
                subcategory=subcategory,
                difficulty_level=difficulty_level,
                is_active=is_active,
                limit=limit,
                offset=offset
            )
            
            response = await self.get_exercises_use_case.execute(request)
            
            return response.to_dict()
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener ejercicios: {str(e)}"
            )
    
    async def get_exercise_by_id(self, exercise_id: str) -> dict:
        """
        Obtiene un ejercicio específico por ID.
        
        Args:
            exercise_id: ID del ejercicio (UUID o exercise_id)
        
        Returns:
            dict: Datos del ejercicio
        
        Raises:
            HTTPException: Si no se encuentra o hay error
        """
        try:
            request = GetExerciseByIdRequest(exercise_id=exercise_id)
            response = await self.get_exercise_by_id_use_case.execute(request)
            
            if not response.found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ejercicio '{exercise_id}' no encontrado"
                )
            
            return response.to_dict()
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener ejercicio: {str(e)}"
            )
    
    async def get_exercise_details(self, exercise_id: str) -> dict:
        """
        Obtiene detalles completos de un ejercicio incluyendo relacionados.
        
        Args:
            exercise_id: ID del ejercicio
        
        Returns:
            dict: Detalles completos del ejercicio
        
        Raises:
            HTTPException: Si no se encuentra o hay error
        """
        try:
            details = await self.get_exercise_details_use_case.execute(exercise_id)
            return details
            
        except ValueError as e:
            # ValueError desde el use case indica que no se encontró
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener detalles: {str(e)}"
            )
    
    async def get_reference_features(self, exercise_id: str) -> dict:
        """
        Obtiene features precalculadas del audio de referencia.
        
        Args:
            exercise_id: ID del ejercicio
        
        Returns:
            dict: Features de referencia
        
        Raises:
            HTTPException: Si no se encuentra o hay error
        """
        try:
            request = GetReferenceFeaturesRequest(exercise_id=exercise_id)
            response = await self.get_reference_features_use_case.execute(request)
            
            if not response.exercise_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ejercicio '{exercise_id}' no encontrado"
                )
            
            if not response.found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Features no disponibles para el ejercicio '{exercise_id}'"
                )
            
            return response.to_dict()
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener features: {str(e)}"
            )
    
    async def get_features_for_comparison(self, exercise_id: str) -> dict:
        """
        Obtiene features optimizadas para comparación DTW.
        
        Args:
            exercise_id: ID del ejercicio
        
        Returns:
            dict: Features esenciales para comparación
        
        Raises:
            HTTPException: Si no se encuentra o hay error
        """
        try:
            features = await self.get_features_for_comparison_use_case.execute(exercise_id)
            
            if not features:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Features no disponibles para el ejercicio '{exercise_id}'"
                )
            
            return features
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener features: {str(e)}"
            )


class ExerciseHealthController:
    """
    Controlador para endpoints de salud y monitoreo.
    """
    
    def __init__(
        self,
        exercise_repository,
        reference_features_repository
    ):
        self.exercise_repository = exercise_repository
        self.reference_features_repository = reference_features_repository
    
    async def health_check(self) -> dict:
        """
        Verifica el estado del módulo de ejercicios.
        
        Returns:
            dict: Estado de salud
        """
        try:
            # Contar ejercicios activos
            exercises_count = await self.exercise_repository.count(is_active=True)
            
            # Contar features cacheadas
            cached_features_count = await self.reference_features_repository.count_cached()
            
            return {
                "status": "healthy",
                "exercises_count": exercises_count,
                "cached_features_count": cached_features_count,
                "cache_coverage": (
                    f"{(cached_features_count / exercises_count * 100):.1f}%"
                    if exercises_count > 0 else "0%"
                )
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_statistics(self) -> dict:
        """
        Obtiene estadísticas del módulo de ejercicios.
        
        Returns:
            dict: Estadísticas
        """
        try:
            # Estadísticas por categoría
            from src.exercises.domain.models.exercise import ExerciseCategory
            
            stats_by_category = {}
            for category in ExerciseCategory:
                count = await self.exercise_repository.count(
                    category=category,
                    is_active=True
                )
                stats_by_category[category.value] = count
            
            # Total de ejercicios
            total = await self.exercise_repository.count(is_active=True)
            
            # Features cacheadas
            cached_count = await self.reference_features_repository.count_cached()
            
            return {
                "total_exercises": total,
                "exercises_by_category": stats_by_category,
                "cached_features": cached_count,
                "cache_coverage_percentage": (
                    round(cached_count / total * 100, 2)
                    if total > 0 else 0
                )
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener estadísticas: {str(e)}"
            )

