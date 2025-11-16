"""
ProcessAudioUseCase - Procesa audio del usuario y guarda attempt.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from src.audio_processing.application.services.audio_processing_service import AudioProcessingService


@dataclass
class ProcessAudioRequest:
    """Request para procesar audio"""
    user_id: str
    exercise_id: str
    audio_base64: str
    metadata: Dict
    reference_text: Optional[str] = None


class ProcessAudioUseCase:
    """
    Caso de uso: Procesar audio del usuario.
    """
    
    def __init__(self, audio_processing_service: AudioProcessingService):
        self.audio_processing_service = audio_processing_service
    
    async def execute(self, request: ProcessAudioRequest) -> Dict:
        """
        Ejecuta el caso de uso.
        
        Args:
            request: Request con audio y metadata
        
        Returns:
            Dict con resultado del procesamiento incluyendo scores de ML
        
        Raises:
            ValueError: Si el audio no pasa las validaciones
        """
        # El service ya retorna un dict completo con scores
        result = await self.audio_processing_service.process_audio_complete(
            audio_base64=request.audio_base64,
            user_id=request.user_id,
            exercise_id=request.exercise_id,
            reference_text=request.reference_text
        )
        
        # El result ya incluye:
        # - attempt_id
        # - scores (pronunciation, fluency, rhythm, overall)
        # - quality_check
        # - processing_time_ms
        # - status
        return result