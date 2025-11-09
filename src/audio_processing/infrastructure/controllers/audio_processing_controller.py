"""
AudioProcessingController - Maneja requests HTTP de audio processing.

Responsabilidades:
- Validar requests HTTP
- Invocar use cases
- Formatear responses HTTP
- Manejar errores
"""

from typing import Dict, Optional
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class AudioProcessingController:
    """
    Controlador de audio processing.
    
    Actúa como adaptador entre HTTP (FastAPI) y los casos de uso.
    """
    
    def __init__(
        self,
        process_audio_use_case,
        validate_audio_use_case
    ):
        self.process_audio_use_case = process_audio_use_case
        self.validate_audio_use_case = validate_audio_use_case
    
    async def process_audio(
        self,
        user_id: str,
        exercise_id: str,
        audio_base64: str,
        metadata: Dict
    ) -> dict:
        """
        Procesa audio del usuario.
        
        Args:
            user_id: ID del usuario
            exercise_id: ID del ejercicio
            audio_base64: Audio en base64
            metadata: Metadata del dispositivo
        
        Returns:
            dict: Resultado del procesamiento
        
        Raises:
            HTTPException: Si hay errores
        """
        try:
            logger.info(f"🎤 Controller: Procesando audio")
            logger.info(f"   User: {user_id}")
            logger.info(f"   Exercise: {exercise_id}")
            logger.info(f"   Audio size: {len(audio_base64)} chars")
            
            # Importar request aquí para evitar circular imports
            from src.audio_processing.application.use_cases.process_audio_use_case import (
                ProcessAudioRequest
            )
            
            # Crear request para el use case
            request = ProcessAudioRequest(
                user_id=user_id,
                exercise_id=exercise_id,
                audio_base64=audio_base64,
                metadata=metadata
            )
            
            # Ejecutar use case (SIN argumentos extra como daily_limit)
            response = await self.process_audio_use_case.execute(request)
            
            logger.info(f"✅ Audio procesado: attempt_id={response.attempt_id}")
            
            return {
                "success": True,
                "data": response.to_dict()
            }
            
        except ValueError as e:
            # Errores de validación (audio rechazado, ejercicio no existe, etc.)
            logger.warning(f"⚠️ Error de validación: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        except HTTPException:
            # Re-raise HTTPExceptions
            raise
        
        except Exception as e:
            # Errores inesperados
            logger.error(f"❌ Error inesperado procesando audio: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error interno al procesar audio: {str(e)}"
            )
    
    async def validate_audio_quality(self, audio_base64: str) -> dict:
        """
        Valida calidad del audio sin procesarlo completamente.
        
        Args:
            audio_base64: Audio en base64
        
        Returns:
            dict: Resultado de la validación
        
        Raises:
            HTTPException: Si hay errores
        """
        try:
            logger.info(f"🔍 Controller: Validando calidad")
            logger.info(f"   Audio size: {len(audio_base64)} chars")
            
            # Importar request aquí
            from src.audio_processing.application.use_cases.validate_audio_quality_use_case import (
                ValidateAudioQualityRequest
            )
            
            # Crear request
            request = ValidateAudioQualityRequest(
                audio_base64=audio_base64
            )
            
            # Ejecutar use case
            response = await self.validate_audio_use_case.execute(request)
            
            logger.info(f"✅ Validación completada: valid={response.is_valid}")
            
            return {
                "success": True,
                "data": response.to_dict()
            }
            
        except ValueError as e:
            logger.warning(f"⚠️ Error de validación: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"❌ Error inesperado validando audio: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al validar audio: {str(e)}"
            )


class AttemptController:
    """
    Controlador de attempts (historial de intentos).
    """
    
    def __init__(
        self,
        get_attempts_use_case,
        get_attempt_by_id_use_case,
        get_progress_use_case
    ):
        self.get_attempts_use_case = get_attempts_use_case
        self.get_attempt_by_id_use_case = get_attempt_by_id_use_case
        self.get_progress_use_case = get_progress_use_case
    
    async def get_user_attempts(
        self,
        user_id: str,
        exercise_id: Optional[str] = None,
        days: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> dict:
        """
        Obtiene el historial de intentos del usuario.
        
        Args:
            user_id: ID del usuario
            exercise_id: Filtrar por ejercicio (opcional)
            days: Últimos N días (opcional)
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            dict: Lista de attempts
        """
        try:
            logger.info(f"📋 Controller: Obteniendo attempts de user {user_id}")
            
            from src.audio_processing.application.use_cases.get_attempts_use_case import (
                GetUserAttemptsRequest
            )
            
            request = GetUserAttemptsRequest(
                user_id=user_id,
                exercise_id=exercise_id,
                days=days,
                limit=limit,
                offset=offset
            )
            
            response = await self.get_attempts_use_case.execute(request)
            
            return {
                "success": True,
                "data": response.to_dict()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo attempts: {str(e)}", exc_info=True)
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
        Obtiene un intento específico por ID.
        
        Args:
            attempt_id: ID del intento
            user_id: ID del usuario (para validar permisos)
        
        Returns:
            dict: Detalle del attempt
        """
        try:
            logger.info(f"📋 Controller: Obteniendo attempt {attempt_id}")
            
            from src.audio_processing.application.use_cases.get_attempts_use_case import (
                GetAttemptByIdRequest
            )
            
            request = GetAttemptByIdRequest(
                attempt_id=attempt_id,
                user_id=user_id
            )
            
            response = await self.get_attempt_by_id_use_case.execute(request)
            
            if not response.found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Intento {attempt_id} no encontrado"
                )
            
            return {
                "success": True,
                "data": response.to_dict()
            }
            
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo attempt: {str(e)}", exc_info=True)
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
        Obtiene resumen de progreso del usuario.
        
        Args:
            user_id: ID del usuario
            days: Últimos N días
        
        Returns:
            dict: Resumen de progreso
        """
        try:
            logger.info(f"📊 Controller: Obteniendo progreso de user {user_id}")
            
            from src.audio_processing.application.use_cases.get_user_progress_use_case import (
                GetUserProgressRequest
            )
            
            request = GetUserProgressRequest(
                user_id=user_id,
                days=days
            )
            
            response = await self.get_progress_use_case.execute(request)
            
            return {
                "success": True,
                "data": response.to_dict()
            }
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo progreso: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener progreso: {str(e)}"
            )