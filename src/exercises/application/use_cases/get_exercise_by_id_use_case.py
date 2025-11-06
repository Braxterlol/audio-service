"""
GetExerciseByIdUseCase - Caso de uso para obtener un ejercicio específico por ID.
"""

from dataclasses import dataclass
from typing import Optional
from src.exercises.domain.models.exercise import Exercise
from src.exercises.domain.repositories.exercise_repository import ExerciseRepository


@dataclass
class GetExerciseByIdRequest:
    """DTO para la petición"""
    exercise_id: str  # Puede ser UUID o exercise_id


@dataclass
class GetExerciseByIdResponse:
    """DTO para la respuesta"""
    exercise: Optional[Exercise]
    found: bool
    
    def to_dict(self) -> dict:
        if not self.found or not self.exercise:
            return {
                "found": False,
                "exercise": None
            }
        
        return {
            "found": True,
            "exercise": self.exercise.to_dict()
        }


class GetExerciseByIdUseCase:
    """
    Caso de uso: Obtener un ejercicio específico por su ID.
    
    Intenta buscar primero por exercise_id (ej: "fonema_r_suave_1"),
    si no encuentra, busca por UUID.
    """
    
    def __init__(self, exercise_repository: ExerciseRepository):
        self.exercise_repository = exercise_repository
    
    async def execute(self, request: GetExerciseByIdRequest) -> GetExerciseByIdResponse:
        """
        Ejecuta el caso de uso.
        
        Args:
            request: ID del ejercicio a buscar
        
        Returns:
            GetExerciseByIdResponse: Ejercicio encontrado o None
        
        Raises:
            ValueError: Si el ID está vacío
        """
        # Validación
        if not request.exercise_id or not request.exercise_id.strip():
            raise ValueError("El exercise_id no puede estar vacío")
        
        exercise_id = request.exercise_id.strip()
        
        # Intentar buscar por exercise_id primero (más común)
        exercise = await self.exercise_repository.find_by_exercise_id(exercise_id)
        
        # Si no encuentra, intentar buscar por UUID
        if not exercise:
            exercise = await self.exercise_repository.find_by_id(exercise_id)
        
        return GetExerciseByIdResponse(
            exercise=exercise,
            found=exercise is not None
        )


class GetExerciseDetailsUseCase:
    """
    Caso de uso extendido: Obtener detalles completos de un ejercicio
    incluyendo información adicional útil.
    """
    
    def __init__(self, exercise_repository: ExerciseRepository):
        self.exercise_repository = exercise_repository
        self.get_by_id_use_case = GetExerciseByIdUseCase(exercise_repository)
    
    async def execute(self, exercise_id: str) -> dict:
        """
        Obtiene detalles completos del ejercicio con metadata adicional.
        
        Args:
            exercise_id: ID del ejercicio
        
        Returns:
            dict: Detalles completos del ejercicio
        
        Raises:
            ValueError: Si el ejercicio no existe
        """
        # Obtener ejercicio
        request = GetExerciseByIdRequest(exercise_id=exercise_id)
        response = await self.get_by_id_use_case.execute(request)
        
        if not response.found or not response.exercise:
            raise ValueError(f"Ejercicio {exercise_id} no encontrado")
        
        exercise = response.exercise
        
        # Obtener ejercicios relacionados (misma subcategoría)
        related = await self.exercise_repository.find_all(
            category=exercise.category,
            subcategory=exercise.subcategory,
            limit=5
        )
        
        # Filtrar el ejercicio actual de los relacionados
        related = [ex for ex in related if ex.id != exercise.id]
        
        # Construir respuesta completa
        return {
            **exercise.to_dict(),
            "related_exercises": [
                {
                    "id": ex.id,
                    "exercise_id": ex.exercise_id,
                    "text_content": ex.text_content,
                    "difficulty_level": ex.difficulty_level.value
                }
                for ex in related[:3]  # Máximo 3 relacionados
            ],
            "expected_duration_range": exercise.get_expected_duration_range(),
            "metadata": {
                "is_phoneme_exercise": exercise.is_phoneme_exercise(),
                "is_rhythm_exercise": exercise.is_rhythm_exercise(),
                "is_intonation_exercise": exercise.is_intonation_exercise(),
                "has_target_phonemes": exercise.has_target_phonemes()
            }
        }