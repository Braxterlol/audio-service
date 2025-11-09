"""
Puerto AttemptRepository - Define el contrato para acceder a intentos.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from src.audio_processing.domain.models.attempt import Attempt, AttemptStatus


class AttemptRepository(ABC):
    """
    Interface (puerto) para el repositorio de intentos.
    
    La implementación concreta estará en infrastructure/data/
    """
    
    @abstractmethod
    async def save(self, attempt: Attempt) -> Attempt:
        """
        Guarda un nuevo intento o actualiza uno existente.
        
        Args:
            attempt: Intento a guardar
        
        Returns:
            Attempt: Intento guardado con ID actualizado
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, attempt_id: str) -> Optional[Attempt]:
        """
        Busca un intento por su ID.
        
        Args:
            attempt_id: UUID del intento
        
        Returns:
            Optional[Attempt]: Intento encontrado o None
        """
        pass
    
    @abstractmethod
    async def find_by_user(
        self,
        user_id: str,
        exercise_id: Optional[str] = None,
        status: Optional[AttemptStatus] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Attempt]:
        """
        Busca intentos de un usuario con filtros opcionales.
        
        Args:
            user_id: UUID del usuario
            exercise_id: Filtrar por ejercicio específico
            status: Filtrar por estado
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            List[Attempt]: Lista de intentos encontrados
        """
        pass
    
    @abstractmethod
    async def find_by_exercise(
        self,
        exercise_id: str,
        limit: int = 100
    ) -> List[Attempt]:
        """
        Busca todos los intentos de un ejercicio específico.
        
        Args:
            exercise_id: UUID del ejercicio
            limit: Límite de resultados
        
        Returns:
            List[Attempt]: Lista de intentos
        """
        pass
    
    @abstractmethod
    async def count_by_user(
        self,
        user_id: str,
        status: Optional[AttemptStatus] = None
    ) -> int:
        """
        Cuenta los intentos de un usuario.
        
        Args:
            user_id: UUID del usuario
            status: Filtrar por estado
        
        Returns:
            int: Número de intentos
        """
        pass
    
    @abstractmethod
    async def delete(self, attempt_id: str) -> bool:
        """
        Elimina un intento (soft delete o hard delete).
        
        Args:
            attempt_id: UUID del intento
        
        Returns:
            bool: True si se eliminó correctamente
        """
        pass
    
    @abstractmethod
    async def find_recent_by_user(
        self,
        user_id: str,
        days: int = 7,
        limit: int = 10
    ) -> List[Attempt]:
        """
        Obtiene los intentos recientes de un usuario.
        
        Args:
            user_id: UUID del usuario
            days: Número de días hacia atrás
            limit: Límite de resultados
        
        Returns:
            List[Attempt]: Intentos recientes
        """
        pass
    
    @abstractmethod
    async def find_anomalies_by_user(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Attempt]:
        """
        Obtiene intentos marcados como anómalos de un usuario.
        
        Args:
            user_id: UUID del usuario
            limit: Límite de resultados
        
        Returns:
            List[Attempt]: Intentos anómalos
        """
        pass
    
    @abstractmethod
    async def get_user_statistics(
        self,
        user_id: str,
        category: Optional[str] = None
    ) -> dict:
        """
        Obtiene estadísticas agregadas de un usuario.
        
        Args:
            user_id: UUID del usuario
            category: Filtrar por categoría de ejercicio
        
        Returns:
            dict: Estadísticas (avg_score, total_attempts, etc.)
        """
        pass
    
    @abstractmethod
    async def update_scores(
        self,
        attempt_id: str,
        overall_score: float,
        phoneme_score: float,
        rhythm_score: float,
        intonation_score: float,
        dtw_distance: float,
        dtw_normalized: float
    ) -> bool:
        """
        Actualiza los scores de un intento (llamado por ML Analysis Service).
        
        Args:
            attempt_id: UUID del intento
            overall_score: Score general
            phoneme_score: Score de fonemas
            rhythm_score: Score de ritmo
            intonation_score: Score de entonación
            dtw_distance: Distancia DTW cruda
            dtw_normalized: Distancia DTW normalizada
        
        Returns:
            bool: True si se actualizó correctamente
        """
        pass


class AttemptQueryRepository(ABC):
    """
    Repositorio de consultas complejas para intentos (CQRS pattern).
    Opcional: Separar comandos (save, delete) de queries (find).
    """
    
    @abstractmethod
    async def get_progress_timeline(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]:
        """
        Obtiene línea de tiempo de progreso para gráficas.
        
        Args:
            user_id: UUID del usuario
            start_date: Fecha de inicio
            end_date: Fecha de fin
        
        Returns:
            List[dict]: Puntos de datos para gráfica
        """
        pass
    
    @abstractmethod
    async def get_attempts_by_score_range(
        self,
        user_id: str,
        min_score: float,
        max_score: float,
        limit: int = 20
    ) -> List[Attempt]:
        """
        Busca intentos dentro de un rango de score.
        
        Args:
            user_id: UUID del usuario
            min_score: Score mínimo
            max_score: Score máximo
            limit: Límite de resultados
        
        Returns:
            List[Attempt]: Intentos en el rango
        """
        pass