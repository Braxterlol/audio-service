# src/exercise_progression/domain/repositories/user_exercise_progress_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from src.exercise_progression.domain.models.user_exercise_progress import UserExerciseProgress

class UserExerciseProgressRepository(ABC):
    
    @abstractmethod
    async def get_all_by_user(self, user_id: uuid.UUID) -> List[UserExerciseProgress]:
        """Retorna todo el progreso del usuario"""
        pass
    
    @abstractmethod
    async def get_by_user_and_exercise(
        self, 
        user_id: uuid.UUID, 
        exercise_id: uuid.UUID
    ) -> Optional[UserExerciseProgress]:
        """Retorna progreso de un ejercicio específico"""
        pass
    
    @abstractmethod
    async def save(self, progress: UserExerciseProgress) -> UserExerciseProgress:
        """Crea o actualiza progreso"""
        pass
    
    @abstractmethod
    async def initialize_user_progress(self, user_id: uuid.UUID) -> None:
        """
        Inicializa progreso para un usuario nuevo.
        Crea registros para TODOS los ejercicios:
        - Primer ejercicio: status = "available"
        - Resto: status = "locked"
        """
        pass
    
    @abstractmethod
    async def get_completed_count(self, user_id: uuid.UUID) -> int:
        """Cuenta ejercicios completados (best_score >= 70)"""
        pass
    
    @abstractmethod
    async def get_total_stars(self, user_id: uuid.UUID) -> int:
        """Suma total de estrellas"""
        pass
    
    @abstractmethod
    async def unlock_exercise(
        self, 
        user_id: uuid.UUID, 
        exercise_id: uuid.UUID
    ) -> None:
        """Cambia status de "locked" a "available"""
        pass