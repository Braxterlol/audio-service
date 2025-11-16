# src/exercise_progression/domain/repositories/exercise_repository.py

from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from src.exercise_progression.domain.models.exercise import Exercise

class ExerciseRepository(ABC):
    
    @abstractmethod
    async def get_all_ordered(self) -> List[Exercise]:
        """Retorna todos los ejercicios ordenados por order_index ASC"""
        pass
    
    @abstractmethod
    async def get_by_id(self, exercise_id: uuid.UUID) -> Optional[Exercise]:
        """Busca por UUID"""
        pass
    
    @abstractmethod
    async def get_by_exercise_id(self, exercise_id: str) -> Optional[Exercise]:
        """Busca por exercise_id string (ej: 'fonema_r_suave_1')"""
        pass
    
    @abstractmethod
    async def get_by_order_index(self, order_index: int) -> Optional[Exercise]:
        """Busca por posición en el camino"""
        pass
    
    @abstractmethod
    async def get_first_exercise(self) -> Exercise:
        """Retorna el ejercicio con order_index = 1"""
        pass
    
    @abstractmethod
    async def get_by_category(self, category: str) -> List[Exercise]:
        """Retorna ejercicios de una categoría"""
        pass
    
    @abstractmethod
    async def count_total(self) -> int:
        """Cuenta total de ejercicios"""
        pass