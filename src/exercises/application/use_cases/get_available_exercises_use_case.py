"""
GetAvailableExercisesUseCase - Obtener ejercicios disponibles según progreso del usuario.
"""

from dataclasses import dataclass
from typing import List, Optional
from src.exercises.domain.repositories.exercise_repository import ExerciseRepository
from src.exercises.domain.models.exercise import Exercise, ExerciseCategory
from src.audio_processing.infrastructure.data.user_progress_repository import (
    UserProgressRepository,
    UserExerciseProgress,
    ProgressStatus
)


@dataclass
class ExerciseWithProgress:
    """Ejercicio con información de progreso del usuario"""
    exercise: Exercise
    progress: Optional[UserExerciseProgress]
    
    @property
    def status(self) -> str:
        """Estado del ejercicio para el usuario."""
        if self.progress:
            return self.progress.status.value
        return "locked"
    
    @property
    def is_available(self) -> bool:
        """Si el usuario puede intentar este ejercicio."""
        if self.progress:
            return self.progress.is_available
        return False
    
    @property
    def best_score(self) -> Optional[float]:
        """Mejor score obtenido."""
        if self.progress:
            return self.progress.best_score
        return None
    
    @property
    def attempts_count(self) -> int:
        """Cantidad de intentos realizados."""
        if self.progress:
            return self.progress.attempts_count
        return 0
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para respuestas JSON."""
        return {
            "exercise_id": self.exercise.exercise_id,
            "category": self.exercise.category.value,
            "subcategory": self.exercise.subcategory,
            "text_content": self.exercise.text_content,
            "difficulty_level": self.exercise.difficulty_level.value,
            "target_phonemes": self.exercise.target_phonemes,
            "reference_audio_url": self.exercise.reference_audio_url,
            "status": self.status,
            "best_score": round(self.best_score, 2) if self.best_score else None,
            "attempts_count": self.attempts_count,
            "is_available": self.is_available
        }


@dataclass
class GetAvailableExercisesRequest:
    """Request para obtener ejercicios disponibles"""
    user_id: str
    category: Optional[ExerciseCategory] = None
    include_locked: bool = False


@dataclass
class GetAvailableExercisesResponse:
    """Response con ejercicios y su estado de progreso"""
    exercises: List[ExerciseWithProgress]
    summary: dict
    
    def to_dict(self) -> dict:
        return {
            "exercises": [ex.to_dict() for ex in self.exercises],
            "summary": self.summary
        }


class GetAvailableExercisesUseCase:
    """
    Caso de uso: Obtener ejercicios disponibles según progreso del usuario.
    """
    
    def __init__(
        self,
        exercise_repository: ExerciseRepository,
        progress_repository: UserProgressRepository
    ):
        self.exercise_repository = exercise_repository
        self.progress_repository = progress_repository
    
    async def execute(
        self,
        request: GetAvailableExercisesRequest
    ) -> GetAvailableExercisesResponse:
        """
        Ejecuta el caso de uso.
        
        Args:
            request: Parámetros de consulta
        
        Returns:
            GetAvailableExercisesResponse: Ejercicios con estado de progreso
        """
        # 1. Obtener todos los ejercicios activos
        all_exercises = await self.exercise_repository.find_all(
            category=request.category,
            is_active=True,
            limit=100
        )
        
        # 2. Obtener progreso del usuario
        user_progress_list = await self.progress_repository.find_by_user(request.user_id)
        
        # 3. Si el usuario no tiene progreso, inicializarlo
        if not user_progress_list:
            await self.progress_repository.initialize_user_progress(request.user_id)
            user_progress_list = await self.progress_repository.find_by_user(request.user_id)
        
        # 4. Crear mapa de progreso
        progress_map = {p.exercise_id: p for p in user_progress_list}
        
        # 5. Combinar ejercicios con progreso
        exercises_with_progress = []
        for exercise in all_exercises:
            progress = progress_map.get(exercise.exercise_id)
            exercises_with_progress.append(
                ExerciseWithProgress(exercise=exercise, progress=progress)
            )
        
        # 6. Filtrar según include_locked
        if not request.include_locked:
            exercises_with_progress = [
                ex for ex in exercises_with_progress if ex.is_available
            ]
        
        # 7. Agrupar por categoría y ordenar
        exercises_with_progress = self._sort_exercises(exercises_with_progress)
        
        # 8. Calcular resumen
        summary = self._calculate_summary(exercises_with_progress, user_progress_list)
        
        return GetAvailableExercisesResponse(
            exercises=exercises_with_progress,
            summary=summary
        )
    
    def _sort_exercises(
        self,
        exercises: List[ExerciseWithProgress]
    ) -> List[ExerciseWithProgress]:
        """Ordena ejercicios por categoría y dificultad."""
        return sorted(
            exercises,
            key=lambda e: (
                e.exercise.category.value,
                e.exercise.subcategory,
                e.exercise.difficulty_level.value,
                e.exercise.exercise_id
            )
        )
    
    def _calculate_summary(
        self,
        exercises: List[ExerciseWithProgress],
        all_progress: List[UserExerciseProgress]
    ) -> dict:
        """Calcula resumen de progreso."""
        total = len(exercises)
        unlocked = sum(1 for ex in exercises if ex.status != "locked")
        completed = sum(1 for ex in exercises if ex.status in ["completed", "mastered"])
        
        # Por categoría
        by_category = {}
        for ex in exercises:
            cat = ex.exercise.category.value
            if cat not in by_category:
                by_category[cat] = {
                    "total": 0,
                    "unlocked": 0,
                    "completed": 0
                }
            by_category[cat]["total"] += 1
            if ex.status != "locked":
                by_category[cat]["unlocked"] += 1
            if ex.status in ["completed", "mastered"]:
                by_category[cat]["completed"] += 1
        
        # Score promedio
        scores = [p.best_score for p in all_progress if p.best_score is not None]
        avg_score = sum(scores) / len(scores) if scores else None
        
        return {
            "total_exercises": total,
            "unlocked_count": unlocked,
            "completed_count": completed,
            "average_score": round(avg_score, 2) if avg_score else None,
            "by_category": by_category
        }