"""
Puerto AudioFeaturesRepository - Define el contrato para acceder a features de audio.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from src.audio_processing.domain.models.audio_features import AudioFeatures


class AudioFeaturesRepository(ABC):
    """
    Interface (puerto) para el repositorio de audio features.
    
    Las features se guardan en MongoDB.
    La implementación concreta estará en infrastructure/data/
    """
    
    @abstractmethod
    async def save(self, features: AudioFeatures) -> AudioFeatures:
        """
        Guarda features de audio en MongoDB.
        
        Args:
            features: Features a guardar
        
        Returns:
            AudioFeatures: Features guardadas
        """
        pass
    
    @abstractmethod
    async def find_by_attempt_id(self, attempt_id: str) -> Optional[AudioFeatures]:
        """
        Busca features por ID de intento.
        
        Args:
            attempt_id: UUID del intento
        
        Returns:
            Optional[AudioFeatures]: Features encontradas o None
        """
        pass
    
    @abstractmethod
    async def find_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[AudioFeatures]:
        """
        Busca features de un usuario.
        
        Args:
            user_id: UUID del usuario
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            List[AudioFeatures]: Lista de features
        """
        pass
    
    @abstractmethod
    async def find_by_exercise(
        self,
        exercise_id: str,
        limit: int = 100
    ) -> List[AudioFeatures]:
        """
        Busca features de un ejercicio específico.
        
        Args:
            exercise_id: ID del ejercicio
            limit: Límite de resultados
        
        Returns:
            List[AudioFeatures]: Lista de features
        """
        pass
    
    @abstractmethod
    async def delete(self, attempt_id: str) -> bool:
        """
        Elimina features de un intento.
        
        Args:
            attempt_id: UUID del intento
        
        Returns:
            bool: True si se eliminó
        """
        pass
    
    @abstractmethod
    async def exists(self, attempt_id: str) -> bool:
        """
        Verifica si existen features para un intento.
        
        Args:
            attempt_id: UUID del intento
        
        Returns:
            bool: True si existen
        """
        pass
    
    @abstractmethod
    async def count_by_user(self, user_id: str) -> int:
        """
        Cuenta las features guardadas de un usuario.
        
        Args:
            user_id: UUID del usuario
        
        Returns:
            int: Número de features
        """
        pass
    
    @abstractmethod
    async def get_storage_stats(self) -> dict:
        """
        Obtiene estadísticas de almacenamiento.
        
        Returns:
            dict: Estadísticas (total_documents, total_size_mb, etc.)
        """
        pass
    
    @abstractmethod
    async def find_for_ml_training(
        self,
        exercise_id: Optional[str] = None,
        min_quality_score: float = 7.0,
        limit: int = 1000
    ) -> List[AudioFeatures]:
        """
        Obtiene features de alta calidad para entrenar modelos ML.
        
        Args:
            exercise_id: Filtrar por ejercicio
            min_quality_score: Calidad mínima
            limit: Límite de resultados
        
        Returns:
            List[AudioFeatures]: Features de alta calidad
        """
        pass