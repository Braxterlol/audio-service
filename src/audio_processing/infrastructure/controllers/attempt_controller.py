"""
AttemptController - Controlador para endpoints de intentos y progreso.
"""

from typing import Optional
from fastapi import HTTPException, status
from src.audio_processing.application.use_cases.get_attempts_use_case import (
    GetUserAttemptsUseCase,
    GetUserAttemptsRequest,
    GetUserAttemptsResponse,
    GetAttemptByIdUseCase,
    GetAttemptByIdRequest,
    GetAttemptByIdResponse
)
from src.audio_processing.application.use_cases.get_user_progress_use_case import (
    GetUserProgressUseCase,
    GetUserProgressRequest,
    GetUserProgressResponse
)
from src.audio_processing.domain.models.attempt import AttemptStatus


class AttemptController:
    """
    Controlador para operaciones de intentos y progreso.
    
    Responsabilidad: Orquestar use cases y manejar errores HTTP.
    """
    
    def __init__(
        self,
        get_attempts_use_case: GetUserAttemptsUseCase,
        get_attempt_by_id_use_case: GetAttemptByIdUseCase,
        get_progress_use_case: GetUserProgressUseCase
    ):
        self.get_attempts_use_case = get_attempts_use_case
        self.get_attempt_by_id_use_case = get_attempt_by_id_use_case
        self.get_progress_use_case = get_progress_use_case
    
    async def get_user_attempts(
        self,
        user_id: str,
        exercise_id: Optional[str] = None,
        status: Optional[str] = None,
        days: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> dict:
        """
        Obtiene el historial de intentos del usuario.
        
        Args:
            user_id: UUID del usuario (viene del token JWT)
            exercise_id: Filtrar por ejercicio
            status: Filtrar por estado
            days: Últimos N días
            limit: Máximo de resultados
            offset: Offset para paginación
        
        Returns:
            dict: Lista de intentos con paginación
        
        Raises:
            HTTPException: Si hay error
        """
        try:
            # Validar y convertir status si viene
            attempt_status = None
            if status:
                try:
                    attempt_status = AttemptStatus(status)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Estado inválido: {status}. Valores válidos: completed, quality_rejected, pending_analysis"
                    )
            
            # Crear request
            request = GetUserAttemptsRequest(
                user_id=user_id,
                exercise_id=exercise_id,
                status=attempt_status,
                days=days,
                limit=min(limit, 100),  # Max 100 resultados
                offset=offset
            )
            
            # Ejecutar use case
            response: GetUserAttemptsResponse = await self.get_attempts_use_case.execute(
                request
            )
            
            # Retornar respuesta
            return {
                "success": True,
                "data": response.to_dict()
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener intentos: {str(e)}"
            )
    
    async def get_attempt_by_id(
        self,
        attempt_id: str,
        user_id: str
    ) -> dict:
        """
        Obtiene el detalle de un intento específico.
        
        Args:
            attempt_id: UUID del intento
            user_id: UUID del usuario (viene del token JWT)
        
        Returns:
            dict: Detalle del intento
        
        Raises:
            HTTPException: Si el intento no existe o no pertenece al usuario
        """
        try:
            # Crear request
            request = GetAttemptByIdRequest(
                attempt_id=attempt_id,
                user_id=user_id
            )
            
            # Ejecutar use case
            response: GetAttemptByIdResponse = await self.get_attempt_by_id_use_case.execute(
                request
            )
            
            # Retornar respuesta
            return {
                "success": True,
                "data": response.to_dict()
            }
        
        except ValueError as e:
            # Intento no encontrado o sin permisos
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener intento: {str(e)}"
            )
    
    async def get_user_progress(
        self,
        user_id: str,
        days: int = 30
    ) -> dict:
        """
        Obtiene el progreso y estadísticas del usuario.
        
        Args:
            user_id: UUID del usuario (viene del token JWT)
            days: Período de análisis (últimos N días)
        
        Returns:
            dict: Progreso y estadísticas
        
        Raises:
            HTTPException: Si hay error
        """
        try:
            # Validar días
            if days < 1 or days > 365:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El período debe estar entre 1 y 365 días"
                )
            
            # Crear request
            request = GetUserProgressRequest(
                user_id=user_id,
                days=days
            )
            
            # Ejecutar use case
            response: GetUserProgressResponse = await self.get_progress_use_case.execute(
                request
            )
            
            # Retornar respuesta
            return {
                "success": True,
                "data": response.to_dict()
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener progreso: {str(e)}"
            )
    