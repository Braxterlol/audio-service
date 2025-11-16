# src/exercise_progression/application/use_cases/validate_exercise_access_use_case.py

import uuid
from src.exercise_progression.application.services.exercise_progression_service import ExerciseProgressionService


class ValidateExerciseAccessUseCase:
    """
    Use Case: Validar si un usuario puede acceder a un ejercicio.
    """
    
    def __init__(self, progression_service: ExerciseProgressionService):
        self.progression_service = progression_service
    
    async def execute(self, user_id: uuid.UUID, exercise_id: uuid.UUID) -> bool:
        """
        Valida acceso.
        
        Returns:
            True si puede acceder, False si está bloqueado
        """
        return await self.progression_service.can_access_exercise(user_id, exercise_id)