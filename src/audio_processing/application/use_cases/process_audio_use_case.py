"""
ProcessAudioUseCase - Procesa audio del usuario y guarda attempt.

IMPORTANTE: Convierte TODOS los numpy types a Python types antes de retornar el Response.
"""

from dataclasses import dataclass
from typing import Dict
import numpy as np
from src.audio_processing.application.services.audio_processing_service import AudioProcessingService


@dataclass
class ProcessAudioRequest:
    """Request para procesar audio"""
    user_id: str
    exercise_id: str
    audio_base64: str
    metadata: Dict


@dataclass
class ProcessAudioResponse:
    """Response del procesamiento de audio"""
    attempt_id: str
    status: str
    quality_check: dict
    basic_metrics: dict
    features_stored: dict
    processing_info: dict
    message: str
    
    def to_dict(self) -> dict:
        return {
            "attempt_id": self.attempt_id,
            "status": self.status,
            "quality_check": self.quality_check,
            "basic_metrics": self.basic_metrics,
            "features_stored": self.features_stored,
            "processing_info": self.processing_info,
            "message": self.message
        }


class ProcessAudioUseCase:
    """
    Caso de uso: Procesar audio del usuario.
    """
    
    def __init__(self, audio_processing_service: AudioProcessingService):
        self.audio_processing_service = audio_processing_service
    
    @staticmethod
    def _to_python_type(value):
        """
        Convierte cualquier tipo de numpy a tipo nativo de Python.
        Esto es crítico para que FastAPI pueda serializar a JSON.
        """
        if value is None:
            return None
        
        # Numpy bool
        if isinstance(value, (np.bool_, bool)):
            return bool(value)
        
        # Numpy float
        if isinstance(value, (np.floating, np.float64, np.float32, np.float16)):
            return float(value)
        
        # Numpy int
        if isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(value)
        
        # Numpy array
        if isinstance(value, np.ndarray):
            return value.tolist()
        
        # Si ya es un tipo nativo, retornarlo tal cual
        return value
    
    def _convert_dict_values(self, d: dict) -> dict:
        """Convierte todos los valores de un diccionario a tipos nativos de Python"""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = self._convert_dict_values(value)
            elif isinstance(value, list):
                result[key] = [self._to_python_type(v) for v in value]
            else:
                result[key] = self._to_python_type(value)
        return result
    
    async def execute(self, request: ProcessAudioRequest) -> ProcessAudioResponse:
        """
        Ejecuta el caso de uso.
        
        Args:
            request: Request con audio y metadata
        
        Returns:
            ProcessAudioResponse: Resultado del procesamiento
        
        Raises:
            ValueError: Si el audio no pasa las validaciones
        """
        # Delegar TODO el procesamiento al Service
        attempt, audio_features, quality_check = await self.audio_processing_service.process_audio_complete(
            audio_base64=request.audio_base64,
            user_id=request.user_id,
            exercise_id=request.exercise_id
        )
        
        # ✅ Construir respuesta convirtiendo TODOS los valores a tipos nativos de Python
        return ProcessAudioResponse(
            attempt_id=str(attempt.id),  # Asegurar que sea string
            status="success",
            quality_check={
                "is_valid": bool(quality_check.is_valid),  # ✅ Convertir a bool nativo
                "quality_score": float(quality_check.quality_score),  # ✅ Convertir a float nativo
                "snr_db": float(quality_check.snr_db) if quality_check.snr_db is not None else None,
                "has_background_noise": bool(quality_check.has_background_noise),  # ✅ Convertir
                "has_clipping": bool(quality_check.has_clipping),  # ✅ Convertir
                "duration_seconds": float(quality_check.duration_seconds),
                "recommendation": str(quality_check.get_recommendation())
            },
            basic_metrics={
                "duration_seconds": float(audio_features.duration_seconds),
                "speech_rate": float(audio_features.rhythm.speech_rate) if audio_features.rhythm else None,
                "pause_count": int(audio_features.rhythm.pause_count) if audio_features.rhythm else 0,
                "articulation_rate": float(audio_features.rhythm.articulation_rate) if audio_features.rhythm else None
            },
            features_stored={
                "features_doc_id": str(attempt.features_doc_id),
                "mongodb_collection": "audio_features",
                "phoneme_count": int(audio_features.phoneme_count) if audio_features.phoneme_count else 0
            },
            processing_info={
                "processing_time_ms": int(attempt.processing_time_ms) if attempt.processing_time_ms else 0,
                "processing_version": str(audio_features.processing_version),
                "status": str(attempt.status.value)
            },
            message="Audio procesado exitosamente. Esperando análisis ML para scores finales."
        )