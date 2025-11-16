# src/exercise_progression/application/use_cases/get_exercise_details_use_case.py

import uuid
from typing import Dict, Optional
from src.exercise_progression.domain.repositories.exercise_repository import ExerciseRepository
from src.exercise_progression.domain.repositories.user_exercise_progress_repository import UserExerciseProgressRepository


class GetExerciseDetailsUseCase:
    """
    Use Case: Obtener detalles de un ejercicio específico.
    """
    
    def __init__(
        self,
        exercise_repo: ExerciseRepository,
        progress_repo: UserExerciseProgressRepository
    ):
        self.exercise_repo = exercise_repo
        self.progress_repo = progress_repo
    
    async def execute(self, user_id: uuid.UUID, exercise_id: str) -> Optional[Dict]:
        """
        Ejecuta el caso de uso.
        
        Args:
            user_id: ID del usuario
            exercise_id: exercise_id string (ej: "fonema_r_suave_1")
        
        Returns:
            Dict con detalles del ejercicio o None si no existe
        """
        # Buscar ejercicio
        exercise = await self.exercise_repo.get_by_exercise_id(exercise_id)
        if not exercise:
            return None
        
        # Buscar progreso del usuario
        progress = await self.progress_repo.get_by_user_and_exercise(
            user_id, exercise.id
        )
        
        return {
            "id": str(exercise.id),
            "exercise_id": exercise.exercise_id,
            "order_index": exercise.order_index,
            "title": self._get_title(exercise),
            "category": exercise.category,
            "subcategory": exercise.subcategory,
            "difficulty_level": exercise.difficulty_level,
            "text_content": exercise.text_content,
            "target_phonemes": exercise.target_phonemes,
            "reference_audio_s3_url": exercise.reference_audio_s3_url,
            "unlock_score_required": 70,
            "tips": self._get_tips(exercise),
            "user_progress": {
                "status": progress.status if progress else "locked",
                "best_score": progress.best_score if progress else None,
                "stars": progress.calculate_stars() if progress else 0,
                "attempts": progress.attempts_count if progress else 0,
                "last_attempt_at": progress.last_attempt_at.isoformat() if progress and progress.last_attempt_at else None
            }
        }
    
    def _get_title(self, exercise) -> str:
        """Genera título legible"""
        if exercise.subcategory:
            subcategory_title = exercise.subcategory.replace("_", " ").title()
            return f"{subcategory_title} - {exercise.text_content}"
        return exercise.text_content
    
    def _get_tips(self, exercise) -> list:
        """Genera tips según el ejercicio"""
        # Puedes personalizar tips por subcategoría
        tips_map = {
            "r_suave": [
                "Coloca la lengua en el paladar",
                "No vibres demasiado",
                "Practica lentamente"
            ],
            "rr_vibrante": [
                "Vibra la lengua con fuerza",
                "Mantén el aire fluyendo",
                "Practica el sonido aislado primero"
            ],
            "s_consonante": [
                "Coloca la lengua cerca de los dientes",
                "Sopla aire suavemente",
                "Mantén el sonido constante"
            ]
        }
        
        return tips_map.get(exercise.subcategory, [
            "Lee el texto despacio",
            "Pronuncia claramente cada palabra",
            "Practica varias veces"
        ])