"""
Puerto ReferenceFeatures Repository - Define el contrato para acceder
a las features precalculadas de los audios de referencia.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from src.exercises.domain.models.reference_features import ReferenceFeatures


class ReferenceFeaturesRepository(ABC):
    """
    Interface (puerto) para el repositorio de features de referencia.
    
    Las features se guardan en MongoDB (o caché Redis).
    La implementación concreta estará en infrastructure/data/
    """
    
    @abstractmethod
    async def find_by_exercise_id(self, exercise_id: str) -> Optional[ReferenceFeatures]:
        """
        Obtiene las features precalculadas de un ejercicio.
        
        Args:
            exercise_id: ID del ejercicio (ej: "fonema_r_suave_1")
        
        Returns:
            Optional[ReferenceFeatures]: Features encontradas o None
        """
        pass
    
    @abstractmethod
    async def save(self, features: ReferenceFeatures) -> ReferenceFeatures:
        """
        Guarda features precalculadas de un ejercicio.
        
        Args:
            features: Features a guardar
        
        Returns:
            ReferenceFeatures: Features guardadas
        """
        pass
    
    @abstractmethod
    async def exists(self, exercise_id: str) -> bool:
        """
        Verifica si existen features precalculadas para un ejercicio.
        
        Args:
            exercise_id: ID del ejercicio
        
        Returns:
            bool: True si existen
        """
        pass
    
    @abstractmethod
    async def delete(self, exercise_id: str) -> bool:
        """
        Elimina features de un ejercicio.
        
        Args:
            exercise_id: ID del ejercicio
        
        Returns:
            bool: True si se eliminó
        """
        pass
    
    @abstractmethod
    async def find_all_cached(self) -> List[ReferenceFeatures]:
        """
        Obtiene todas las features cacheadas.
        
        Returns:
            List[ReferenceFeatures]: Lista de todas las features
        """
        pass
    
    @abstractmethod
    async def count_cached(self) -> int:
        """
        Cuenta cuántos ejercicios tienen features precalculadas.
        
        Returns:
            int: Número de features cacheadas
        """
        pass
    
    @abstractmethod
    async def invalidate_cache(self, exercise_id: str) -> bool:
        """
        Invalida el caché de features de un ejercicio.
        
        Args:
            exercise_id: ID del ejercicio
        
        Returns:
            bool: True si se invalidó
        """
        pass

