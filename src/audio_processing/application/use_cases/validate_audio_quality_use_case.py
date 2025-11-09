"""
ValidateAudioQualityUseCase - Validación rápida de calidad sin procesamiento completo.
"""

from dataclasses import dataclass
from src.audio_processing.application.services.audio_processing_service import AudioProcessingService
from src.audio_processing.domain.models.quality_check import QualityCheck


@dataclass
class ValidateAudioQualityRequest:
    """DTO para la petición"""
    audio_base64: str


@dataclass
class ValidateAudioQualityResponse:
    """DTO para la respuesta"""
    quality_check: QualityCheck
    duration_seconds: float
    
    def to_dict(self) -> dict:
        return {
            **self.quality_check.to_dict(),
            "duration_seconds": round(self.duration_seconds, 2)
        }


class ValidateAudioQualityUseCase:
    """
    Caso de uso: Validar calidad de audio sin procesarlo completamente.
    
    Útil para dar feedback inmediato al usuario en la UI antes de enviar.
    """
    
    def __init__(self, audio_processing_service: AudioProcessingService):
        self.audio_processing_service = audio_processing_service
    
    async def execute(
        self,
        request: ValidateAudioQualityRequest
    ) -> ValidateAudioQualityResponse:
        """
        Ejecuta el caso de uso.
        
        Args:
            request: Audio a validar
        
        Returns:
            ValidateAudioQualityResponse: Resultado de la validación
        """
        # Validar audio
        quality_check, audio = await self.audio_processing_service.validate_audio_only(
            request.audio_base64
        )
        
        return ValidateAudioQualityResponse(
            quality_check=quality_check,
            duration_seconds=audio.metadata.duration_seconds
        )