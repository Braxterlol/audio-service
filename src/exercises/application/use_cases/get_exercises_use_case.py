"""
GetExercisesUseCase - Caso de uso para obtener lista de ejercicios con filtros.
"""

from typing import List, Optional
from dataclasses import dataclass
from src.exercises.domain.models.exercise import Exercise, ExerciseCategory
from src.exercises.domain.repositories.exercise_repository import ExerciseRepository


@dataclass
class GetExercisesRequest:
    """DTO para la petición de obtener ejercicios"""
    category: Optional[str] = None
    subcategory: Optional[str] = None
    difficulty_level: Optional[int] = None
    is_active: bool = True
    limit: int = 50
    offset: int = 0


@dataclass
class GetExercisesResponse:
    """DTO para la respuesta de obtener ejercicios"""
    exercises: List[Exercise]
    total: int
    limit: int
    offset: int
    
    def to_dict(self) -> dict:
        return {
            "exercises": [ex.to_dict() for ex in self.exercises],
            "total": self.total,
            "limit": self.limit,
            "offset": self.offset
        }


class GetExercisesUseCase:
    """
    Caso de uso: Obtener lista de ejercicios con filtros opcionales.
    
    Responsabilidad única: Coordinar la obtención de ejercicios filtrados.
    """
    
    def __init__(self, exercise_repository: ExerciseRepository):
        self.exercise_repository = exercise_repository
    
    async def execute(self, request: GetExercisesRequest) -> GetExercisesResponse:
        """
        Ejecuta el caso de uso.
        
        Args:
            request: Parámetros de filtrado
        
        Returns:
            GetExercisesResponse: Lista de ejercicios
        
        Raises:
            ValueError: Si los parámetros son inválidos
        """
        # Validaciones
        self._validate_request(request)
        
        # Convertir category string a enum
        category_enum = None
        if request.category:
            try:
                category_enum = ExerciseCategory(request.category)
            except ValueError:
                raise ValueError(
                    f"Categoría inválida: {request.category}. "
                    f"Valores permitidos: {[c.value for c in ExerciseCategory]}"
                )
        
        # Obtener ejercicios del repositorio
        exercises = await self.exercise_repository.find_all(
            category=category_enum,
            subcategory=request.subcategory,
            difficulty_level=request.difficulty_level,
            is_active=request.is_active,
            limit=request.limit,
            offset=request.offset
        )
        
        # Contar total (para paginación)
        total = await self.exercise_repository.count(
            category=category_enum,
            is_active=request.is_active
        )
        
        return GetExercisesResponse(
            exercises=exercises,
            total=total,
            limit=request.limit,
            offset=request.offset
        )
    
    def _validate_request(self, request: GetExercisesRequest):
        """Valida los parámetros de la petición"""
        if request.limit < 1 or request.limit > 100:
            raise ValueError("El límite debe estar entre 1 y 100")
        
        if request.offset < 0:
            raise ValueError("El offset no puede ser negativo")
        
        if request.difficulty_level is not None:
            if request.difficulty_level < 1 or request.difficulty_level > 5:
                raise ValueError("El nivel de dificultad debe estar entre 1 y 5")