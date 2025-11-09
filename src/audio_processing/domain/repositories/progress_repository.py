"""
Puerto ProgressRepository - Define el contrato para acceder al progreso del usuario.
"""

from abc import ABC, abstractmethod
from typing import Optional
from src.audio_processing.domain.models.user_progress import UserProgress, ProgressTrend


class ProgressRepository(ABC):
    """
    Interface (puerto) para el repositorio de progreso de usuarios.
    
    La implementación concreta estará en infrastructure/data/
    """
    
    @abstractmethod
    async def save(self, progress: UserProgress) -> UserProgress:
        """
        Guarda o actualiza el progreso de un usuario.
        
        Args:
            progress: Progreso a guardar
        
        Returns:
            UserProgress: Progreso guardado
        """
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> Optional[UserProgress]:
        """
        Busca el progreso de un usuario.
        
        Args:
            user_id: UUID del usuario
        
        Returns:
            Optional[UserProgress]: Progreso encontrado o None
        """
        pass
    
    @abstractmethod
    async def exists(self, user_id: str) -> bool:
        """
        Verifica si existe registro de progreso para un usuario.
        
        Args:
            user_id: UUID del usuario
        
        Returns:
            bool: True si existe
        """
        pass
    
    @abstractmethod
    async def update_scores(
        self,
        user_id: str,
        fonema_avg: Optional[float] = None,
        ritmo_avg: Optional[float] = None,
        entonacion_avg: Optional[float] = None
    ) -> bool:
        """
        Actualiza los scores promedio de un usuario.
        
        Args:
            user_id: UUID del usuario
            fonema_avg: Promedio de fonemas
            ritmo_avg: Promedio de ritmo
            entonacion_avg: Promedio de entonación
        
        Returns:
            bool: True si se actualizó
        """
        pass
    
    @abstractmethod
    async def update_trend(
        self,
        user_id: str,
        trend: ProgressTrend,
        percentage: float
    ) -> bool:
        """
        Actualiza la tendencia de progreso.
        
        Args:
            user_id: UUID del usuario
            trend: Nueva tendencia
            percentage: Porcentaje de cambio
        
        Returns:
            bool: True si se actualizó
        """
        pass
    
    @abstractmethod
    async def update_cluster(
        self,
        user_id: str,
        cluster_id: int,
        profile: str
    ) -> bool:
        """
        Actualiza el cluster ML del usuario.
        
        Args:
            user_id: UUID del usuario
            cluster_id: ID del cluster
            profile: Perfil del cluster
        
        Returns:
            bool: True si se actualizó
        """
        pass
    
    @abstractmethod
    async def increment_attempts(
        self,
        user_id: str,
        category: str,
        was_successful: bool = False,
        was_perfect: bool = False
    ) -> bool:
        """
        Incrementa contadores de intentos.
        
        Args:
            user_id: UUID del usuario
            category: 'fonema', 'ritmo' o 'entonacion'
            was_successful: Si fue exitoso (score >= 70)
            was_perfect: Si fue perfecto (score >= 95)
        
        Returns:
            bool: True si se actualizó
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """
        Elimina el progreso de un usuario.
        
        Args:
            user_id: UUID del usuario
        
        Returns:
            bool: True si se eliminó
        """
        pass
    
    @abstractmethod
    async def get_users_by_cluster(
        self,
        cluster_id: int,
        limit: int = 100
    ) -> list[str]:
        """
        Obtiene los user_ids de un cluster específico.
        
        Args:
            cluster_id: ID del cluster
            limit: Límite de resultados
        
        Returns:
            list[str]: Lista de user_ids
        """
        pass
    
    @abstractmethod
    async def get_progress_summary(self) -> dict:
        """
        Obtiene resumen global de progreso (para analytics).
        
        Returns:
            dict: Estadísticas agregadas de todos los usuarios
        """
        pass