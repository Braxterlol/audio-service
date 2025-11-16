# src/exercise_progression/application/use_cases/get_exercise_map_use_case.py

import uuid
from typing import Dict
from src.exercise_progression.application.services.exercise_progression_service import ExerciseProgressionService


class GetExerciseMapUseCase:
    """
    Use Case: Obtener el mapa completo de ejercicios con estados.
    """
    
    def __init__(self, progression_service: ExerciseProgressionService):
        self.progression_service = progression_service
    
    async def execute(self, user_id: uuid.UUID) -> Dict:
        """
        Ejecuta el caso de uso.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Dict con mapa completo de ejercicios
        """
        return await self.progression_service.get_user_exercise_map(user_id)