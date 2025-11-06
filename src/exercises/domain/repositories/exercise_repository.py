"""
Puerto ExerciseRepository - Define el contrato para acceder a ejercicios.

Este es un puerto (interface) en arquitectura hexagonal.
Define QUÉ operaciones se pueden hacer, no CÓMO se implementan.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.exercises.domain.models.exercise import Exercise, ExerciseCategory


class ExerciseRepository(ABC):
    """
    Interface (puerto) para el repositorio de ejercicios.
    
    La implementación concreta estará en infrastructure/data/
    """
    
    @abstractmethod
    async def find_by_id(self, exercise_id: str) -> Optional[Exercise]:
        """
        Busca un ejercicio por su ID único (UUID).
        
        Args:
            exercise_id: UUID del ejercicio
        
        Returns:
            Optional[Exercise]: Ejercicio encontrado o None
        """
        pass
    
    @abstractmethod
    async def find_by_exercise_id(self, exercise_id: str) -> Optional[Exercise]:
        """
        Busca un ejercicio por su exercise_id (ej: "fonema_r_suave_1").
        
        Args:
            exercise_id: Identificador del ejercicio
        
        Returns:
            Optional[Exercise]: Ejercicio encontrado o None
        """
        pass
    
    @abstractmethod
    async def find_all(
        self,
        category: Optional[ExerciseCategory] = None,
        subcategory: Optional[str] = None,
        difficulty_level: Optional[int] = None,
        is_active: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[Exercise]:
        """
        Busca ejercicios con filtros opcionales.
        
        Args:
            category: Filtrar por categoría
            subcategory: Filtrar por subcategoría
            difficulty_level: Filtrar por dificultad
            is_active: Filtrar por estado activo
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            List[Exercise]: Lista de ejercicios encontrados
        """
        pass
    
    @abstractmethod
    async def count(
        self,
        category: Optional[ExerciseCategory] = None,
        is_active: bool = True
    ) -> int:
        """
        Cuenta ejercicios con filtros opcionales.
        
        Args:
            category: Filtrar por categoría
            is_active: Filtrar por estado activo
        
        Returns:
            int: Número de ejercicios
        """
        pass
    
    @abstractmethod
    async def save(self, exercise: Exercise) -> Exercise:
        """
        Guarda un nuevo ejercicio o actualiza uno existente.
        
        Args:
            exercise: Ejercicio a guardar
        
        Returns:
            Exercise: Ejercicio guardado con ID actualizado
        """
        pass
    
    @abstractmethod
    async def delete(self, exercise_id: str) -> bool:
        """
        Elimina un ejercicio (soft delete).
        
        Args:
            exercise_id: UUID del ejercicio
        
        Returns:
            bool: True si se eliminó correctamente
        """
        pass
    
    @abstractmethod
    async def exists(self, exercise_id: str) -> bool:
        """
        Verifica si existe un ejercicio.
        
        Args:
            exercise_id: Identificador del ejercicio (exercise_id, no UUID)
        
        Returns:
            bool: True si existe
        """
        pass
    
    @abstractmethod
    async def find_by_category_grouped(
        self,
        category: ExerciseCategory
    ) -> dict[str, List[Exercise]]:
        """
        Obtiene ejercicios agrupados por subcategoría.
        
        Args:
            category: Categoría a buscar
        
        Returns:
            dict: Diccionario {subcategoria: [ejercicios]}
        """
        pass

