"""
ProcessAudioUseCase - Procesa audio del usuario y guarda attempt.

Este use case NO calcula scores de ML. Solo:
1. Valida calidad del audio
2. Extrae features básicos
3. Guarda attempt con status=PENDING_ANALYSIS
4. Guarda features en MongoDB

Los scores se calcularán después por el ML Analysis Service.
"""

import time
from dataclasses import dataclass
from typing import Optional, Dict
from src.audio_processing.domain.models.attempt import Attempt, AttemptStatus
from src.audio_processing.domain.models.audio_features import AudioFeatures
from src.audio_processing.domain.repositories.attempt_repository import AttemptRepository
from src.audio_processing.domain.repositories.audio_features_repository import AudioFeaturesRepository
from src.audio_processing.application.services.audio_processing_service import AudioProcessingService
from src.audio_processing.application.services.validation_service import ValidationService
from src.audio_processing.application.use_cases.validate_audio_quality_use_case import ValidateAudioQualityRequest, ValidateAudioQualityResponse


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
    
    Flujo:
    1. Valida calidad del audio
    2. Extrae features acústicos
    3. Guarda attempt con status=PENDING_ANALYSIS (SIN scores)
    4. Guarda features en MongoDB
    5. Retorna métricas básicas
    
    Nota: Los scores (pronunciation, fluency, rhythm) se calcularán
    después por el ML Analysis Service.
    """
    
    def __init__(
        self,
        audio_processing_service: AudioProcessingService,
        validation_service: ValidationService
    ):
        self.audio_processing_service = audio_processing_service
        self.validation_service = validation_service
    
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
        start_time = time.time()
        
        #1. Validar ejercicio existe
        await self.validation_service.validate_exercise_exists(request.exercise_id)
        
        #2. Validar calidad del audio
        validate_audio_quality_request = ValidateAudioQualityRequest(
            audio_base64=request.audio_base64
        )
        validate_audio_quality_response = await self.audio_processing_service.validate_audio_(
            validate_audio_quality_request
        )
        quality_check = validate_audio_quality_response.quality_check(
            request.audio_base64
        )
        
        if not quality_check.is_valid:
            raise ValueError(
                f"Audio rechazado por baja calidad: {quality_check.rejection_reason}"
            )
        
        # 3. Extraer features completos
        audio_features = await self.audio_processing_service.process_audio_complete(
            audio_base64=request.audio_base64,
            exercise_id=request.exercise_id,
            user_id=request.user_id
        )
        
        # 4. Guardar features en MongoDB
        features_doc_id = await self.audio_processing_service.save_audio_features(
            audio_features
        )
        
        # 5. Calcular tiempo de procesamiento
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # 6. Crear Attempt (SIN scores de ML)
        attempt = Attempt.create_new(
            user_id=request.user_id,
            exercise_id=request.exercise_id,
            audio_quality_score=quality_check.quality_score,
            audio_snr_db=quality_check.snr_db,
            has_background_noise=quality_check.has_background_noise,
            has_clipping=quality_check.has_clipping,
            total_duration_seconds=quality_check.duration_seconds,
            speech_rate=audio_features.speech_rate if hasattr(audio_features, 'speech_rate') else None,
            articulation_rate=None,  # Calcular si es necesario
            pause_count=audio_features.pause_count if hasattr(audio_features, 'pause_count') else None,
            features_doc_id=features_doc_id,
            processing_time_ms=processing_time_ms
        )
        
        # 7. Guardar attempt en PostgreSQL
        await self.audio_processing_service.save_attempt(attempt)
        
        # 8. Construir respuesta
        return ProcessAudioResponse(
            attempt_id=attempt.id,
            status="success",
            quality_check={
                # "is_valid": quality_check.is_valid,
                # "quality_score": float(quality_check.quality_score),
                # "snr_db": float(quality_check.snr_db) if quality_check.snr_db else None,
                # "has_background_noise": quality_check.has_background_noise,
                # "has_clipping": quality_check.has_clipping,
                # "duration_seconds": float(quality_check.duration_seconds),
                # "recommendation": quality_check.get_recommendation()
            },
            basic_metrics={
                # "duration_seconds": float(quality_check.duration_seconds),
                "speech_rate": float(audio_features.speech_rate) if hasattr(audio_features, 'speech_rate') else None,
                "pause_count": audio_features.pause_count if hasattr(audio_features, 'pause_count') else 0,
                "energy_mean": float(audio_features.energy_mean) if hasattr(audio_features, 'energy_mean') else None
            },
            features_stored={
                "features_doc_id": features_doc_id,
                "mongodb_collection": "audio_features"
            },
            processing_info={
                "processing_time_ms": processing_time_ms,
                "processing_version": "v1.0",
                "status": attempt.status.value
            },
            message=(
                "Audio procesado exitosamente. "
                "Esperando análisis ML para scores finales."
            )
        )