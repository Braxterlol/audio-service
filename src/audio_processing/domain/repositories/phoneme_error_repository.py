"""
Puerto PhonemeErrorRepository - Define el contrato para acceder a errores fonéticos.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from src.audio_processing.domain.models.phoneme_error import PhonemeError, ErrorType


class PhonemeErrorRepository(ABC):
    """
    Interface (puerto) para el repositorio de errores fonéticos.
    
    La implementación concreta estará en infrastructure/data/
    """
    
    @abstractmethod
    async def save(self, error: PhonemeError) -> PhonemeError:
        """
        Guarda un error fonético.
        
        Args:
            error: Error a guardar
        
        Returns:
            PhonemeError: Error guardado con ID
        """
        pass
    
    @abstractmethod
    async def save_batch(self, errors: List[PhonemeError]) -> List[PhonemeError]:
        """
        Guarda múltiples errores en batch (optimización).
        
        Args:
            errors: Lista de errores
        
        Returns:
            List[PhonemeError]: Errores guardados
        """
        pass
    
    @abstractmethod
    async def find_by_attempt(self, attempt_id: str) -> List[PhonemeError]:
        """
        Busca todos los errores de un intento.
        
        Args:
            attempt_id: UUID del intento
        
        Returns:
            List[PhonemeError]: Lista de errores
        """
        pass
    
    @abstractmethod
    async def find_by_user(
        self,
        user_id: str,
        phoneme: Optional[str] = None,
        error_type: Optional[ErrorType] = None,
        limit: int = 50
    ) -> List[PhonemeError]:
        """
        Busca errores de un usuario con filtros opcionales.
        
        Args:
            user_id: UUID del usuario
            phoneme: Filtrar por fonema específico
            error_type: Filtrar por tipo de error
            limit: Límite de resultados
        
        Returns:
            List[PhonemeError]: Lista de errores
        """
        pass
    
    @abstractmethod
    async def get_user_error_statistics(
        self,
        user_id: str
    ) -> Dict[str, dict]:
        """
        Obtiene estadísticas de errores agregadas por fonema.
        
        Args:
            user_id: UUID del usuario
        
        Returns:
            dict: {
                "/r/": {"count": 15, "avg_severity": 7.2, "most_common_type": "distorsion"},
                ...
            }
        """
        pass
    
    @abstractmethod
    async def get_most_common_errors(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[dict]:
        """
        Obtiene los errores más comunes del usuario.
        
        Args:
            user_id: UUID del usuario
            limit: Límite de resultados
        
        Returns:
            List[dict]: Errores más frecuentes ordenados
        """
        pass
    
    @abstractmethod
    async def count_by_phoneme(
        self,
        user_id: str,
        phoneme: str
    ) -> int:
        """
        Cuenta cuántas veces un usuario ha cometido errores en un fonema.
        
        Args:
            user_id: UUID del usuario
            phoneme: Fonema a consultar
        
        Returns:
            int: Número de errores
        """
        pass
    
    @abstractmethod
    async def delete_by_attempt(self, attempt_id: str) -> int:
        """
        Elimina todos los errores de un intento.
        
        Args:
            attempt_id: UUID del intento
        
        Returns:
            int: Número de errores eliminados
        """
        pass
    
    @abstractmethod
    async def get_error_rate_by_phoneme(
        self,
        user_id: str,
        phoneme: str
    ) -> float:
        """
        Calcula la tasa de error de un fonema específico.
        
        Args:
            user_id: UUID del usuario
            phoneme: Fonema a analizar
        
        Returns:
            float: Tasa de error (0-1)
        """
        pass
    
    @abstractmethod
    async def get_global_error_statistics(self) -> dict:
        """
        Obtiene estadísticas globales de errores (para análisis ML).
        
        Returns:
            dict: Estadísticas agregadas de todos los usuarios
        """
        pass