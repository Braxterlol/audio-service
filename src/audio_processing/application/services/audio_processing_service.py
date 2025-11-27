"""
AudioProcessingService - Servicio de aplicación para procesamiento de audio.

Integrado con ML Analysis Service para obtener scores.
"""

from typing import Dict, Optional
import httpx
import logging
from datetime import datetime
from dataclasses import replace

from src.audio_processing.domain.models.audio import Audio
from src.audio_processing.domain.models.audio_features import AudioFeatures
from src.audio_processing.domain.models.quality_check import QualityCheck
from src.audio_processing.domain.models.attempt import Attempt, AttemptStatus
from src.audio_processing.domain.repositories.attempt_repository import AttemptRepository
from src.audio_processing.domain.repositories.audio_features_repository import AudioFeaturesRepository
from src.audio_processing.infrastructure.helpers.audio_loader import AudioLoader
from src.audio_processing.infrastructure.helpers.audio_validator import AudioValidator
from src.audio_processing.infrastructure.helpers.audio_normalizer import AudioNormalizer
from src.audio_processing.infrastructure.helpers.feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)


class AudioProcessingService:
    """
    Servicio de aplicación para procesamiento de audio.
    """
    
    def __init__(
        self,
        attempt_repository: AttemptRepository,
        audio_features_repository: AudioFeaturesRepository,
        audio_loader: AudioLoader = None,
        audio_validator: AudioValidator = None,
        audio_normalizer: AudioNormalizer = None,
        feature_extractor: FeatureExtractor = None,
        ml_service_url: str = "http://localhost:8002",
        ml_service_api_key: str = "secret_key_12345"
    ):
        self.attempt_repository = attempt_repository
        self.audio_features_repository = audio_features_repository
        
        # Helpers
        self.audio_loader = audio_loader or AudioLoader()
        self.audio_validator = audio_validator or AudioValidator()
        self.audio_normalizer = audio_normalizer or AudioNormalizer()
        self.feature_extractor = feature_extractor or FeatureExtractor()
        
        # ML Service config
        self.ml_service_url = ml_service_url
        self.ml_service_api_key = ml_service_api_key
    
    async def process_audio_complete(
        self,
        audio_base64: str,
        user_id: str,
        exercise_id: str,
        reference_text: Optional[str] = None
    ) -> Dict:
        """
        Procesa un audio completo e integra con ML Service.
        
        FLUJO:
        1. Cargar y validar audio
        2. Si es inválido, guardar attempt rechazado y lanzar error
        3. Normalizar audio
        4. Extraer features
        5. Guardar Attempt (PENDING_ANALYSIS) y AudioFeatures
        6. 🔥 Llamar a ML Service para obtener scores
        7. Actualizar Attempt con scores (COMPLETED)
        8. Retornar resultado completo
        """
        start_time = datetime.utcnow()
        
        # 1. Cargar audio
        audio = self.audio_loader.load_from_base64(audio_base64, source="user")
        
        # 2. Validar calidad
        quality_check = self.audio_validator.validate(audio)
        
        if not quality_check.is_valid:
            # Crear intento fallido
            import uuid as uuid_lib
            attempt = Attempt(
                id=str(uuid_lib.uuid4()),  # Generar UUID como string
                user_id=user_id,
                exercise_id=exercise_id,
                attempted_at=datetime.utcnow(),
                audio_quality_score=quality_check.quality_score,
                audio_snr_db=quality_check.snr_db,
                has_background_noise=quality_check.has_background_noise,
                has_clipping=quality_check.has_clipping,
                total_duration_seconds=quality_check.duration_seconds,
                status=AttemptStatus.QUALITY_REJECTED
            )
            
            # Guardar intento fallido
            attempt = await self.attempt_repository.save(attempt)
            
            raise ValueError(quality_check.rejection_reason)
        
        # 3. Normalizar audio
        audio_normalized = self.audio_normalizer.normalize(
            audio,
            reduce_noise=True,
            trim_silence=True,
            normalize_volume=True
        )
        
        # 4. Extraer features
        features_raw = self.feature_extractor.extract_all_features(
            audio_normalized,
            attempt_id="temp",
            exercise_id=exercise_id,
            user_id=user_id
        )
        
        # 5. Calcular tiempo de procesamiento
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # 6. Crear Attempt (PENDING_ANALYSIS)
        import uuid as uuid_lib
        attempt = Attempt(
            id=str(uuid_lib.uuid4()),  # Generar UUID como string
            user_id=user_id,
            exercise_id=exercise_id,
            attempted_at=start_time,
            audio_quality_score=quality_check.quality_score,
            audio_snr_db=quality_check.snr_db,
            has_background_noise=quality_check.has_background_noise,
            has_clipping=quality_check.has_clipping,
            total_duration_seconds=features_raw.duration_seconds,
            speech_rate=features_raw.rhythm.speech_rate if features_raw.rhythm else None,
            articulation_rate=features_raw.rhythm.articulation_rate if features_raw.rhythm else None,
            pause_count=features_raw.rhythm.pause_count if features_raw.rhythm else None,
            features_doc_id=None,
            processing_time_ms=processing_time,
            status=AttemptStatus.PENDING_ANALYSIS
        )
        
        # 7. Guardar Attempt en PostgreSQL
        attempt = await self.attempt_repository.save(attempt)
        
        # 8. Actualizar AudioFeatures con attempt_id correcto
        audio_features = replace(features_raw, attempt_id=attempt.id)
        
        # 9. Guardar features en MongoDB
        await self.audio_features_repository.save(audio_features)
        
        # 10. Actualizar features_doc_id
        attempt.features_doc_id = attempt.id
        await self.attempt_repository.save(attempt)
        
        # 11. 🔥 LLAMAR A ML SERVICE
        ml_response = None
        try:
            logger.info(f"Llamando a ML Service para attempt: {attempt.id}")
            
            ml_response = await self._call_ml_service(
                attempt_id=attempt.id,
                user_id=user_id,
                exercise_id=exercise_id,
                audio_features=audio_features,
                audio_base64=audio_base64,
                reference_text=reference_text
            )
            
            # 12. Actualizar Attempt con scores del ML Service
            attempt.pronunciation_score = ml_response['scores'].get('pronunciation')
            attempt.fluency_score = ml_response['scores'].get('fluency')
            attempt.rhythm_score = ml_response['scores'].get('rhythm')
            attempt.overall_score = ml_response['scores'].get('overall')
            attempt.status = AttemptStatus.COMPLETED
            attempt.analyzed_at = datetime.utcnow()
            
            # Guardar attempt actualizado
            await self.attempt_repository.save(attempt)
            
            logger.info(f"✅ Attempt {attempt.id} completado con scores")
            
        except Exception as e:
            logger.error(f"❌ Error llamando a ML Service: {e}")
            # Mantener como PENDING_ANALYSIS (no hay estado FAILED)
            # No lanzamos excepción para que el usuario al menos vea el audio procesado
        
        # 13. Retornar resultado completo
        # Construir resultado
        result = {
            "attempt_id": str(attempt.id),  # ← Asegurar que sea string
            "user_id": str(attempt.user_id),
            "exercise_id": str(attempt.exercise_id),
            "status": str(attempt.status.value),
            "scores": {
                "pronunciation": float(attempt.pronunciation_score) if attempt.pronunciation_score is not None else None,
                "fluency": float(attempt.fluency_score) if attempt.fluency_score is not None else None,
                "rhythm": float(attempt.rhythm_score) if attempt.rhythm_score is not None else None,
                "overall": float(attempt.overall_score) if attempt.overall_score is not None else None
            },
            "quality_check": {
                "is_valid": bool(quality_check.is_valid),
                "quality_score": float(quality_check.quality_score),
                "snr_db": float(quality_check.snr_db) if quality_check.snr_db is not None else None,
                "has_background_noise": bool(quality_check.has_background_noise),
                "has_clipping": bool(quality_check.has_clipping),
                "duration_seconds": float(quality_check.duration_seconds)
            },
            "processing_time_ms": int(processing_time),
            "attempted_at": attempt.attempted_at.isoformat(),
            "analyzed_at": attempt.analyzed_at.isoformat() if attempt.analyzed_at else None
        }
        
        # ✅ AGREGAR FEEDBACK Y CONFIDENCE DEL ML SERVICE SI EXISTEN
        if ml_response:
            if "feedback" in ml_response:
                result["feedback"] = ml_response["feedback"]
            if "confidence" in ml_response:
                result["confidence"] = ml_response["confidence"]
            if "model_versions" in ml_response:
                result["model_versions"] = ml_response["model_versions"]
            if "processing_info" in ml_response:
                result["processing_info"] = ml_response["processing_info"]

        # Limpiar cualquier tipo numpy que quede
        return self._clean_numpy_types(result)

    def _clean_numpy_types(self, obj):
            """
            Convierte recursivamente tipos numpy a tipos nativos de Python.
            """
            import numpy as np
            
            if isinstance(obj, dict):
                return {key: self._clean_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [self._clean_numpy_types(item) for item in obj]
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
    
    async def _call_ml_service(
        self,
        attempt_id: str,
        user_id: str,
        exercise_id: str,
        audio_features: AudioFeatures,
        audio_base64: str,
        reference_text: Optional[str] = None
    ) -> Dict:
        """
        Llama al ML Analysis Service para obtener scores.
        
        Args:
            attempt_id: ID del attempt
            user_id: ID del usuario
            exercise_id: ID del ejercicio
            audio_features: Features extraídos
            audio_base64: Audio en base64
            reference_text: Texto esperado (para Azure)
        
        Returns:
            Dict con scores del ML Service
        """
        # Convertir AudioFeatures a dict para enviar al ML Service
        features_dict = self._audio_features_to_dict(audio_features)
        
        payload = {
            "attempt_id": attempt_id,
            "user_id": user_id,
            "exercise_id": exercise_id,
            "audio_features": features_dict,
            "reference_text": reference_text,
            "audio_base64": audio_base64
        }
        
        headers = {
            "X-API-Key": self.ml_service_api_key,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.ml_service_url}/api/v1/ml/analyze",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"ML Service error ({response.status_code}): {response.text}")
    
    def _audio_features_to_dict(self, audio_features: AudioFeatures) -> Dict:
        """Convierte AudioFeatures a dict para el ML Service."""
        prosody_dict = None
        if audio_features.prosody:
            prosody_dict = {
                "jitter": audio_features.prosody.jitter,
                "shimmer": audio_features.prosody.shimmer,
                "f0_stats": audio_features.prosody.f0_stats,  # Ya es dict
                "energy_stats": audio_features.prosody.energy_stats  # Ya es dict
            }
        rhythm_dict = None
        if audio_features.rhythm:
            rhythm_dict = {
                "speech_rate": audio_features.rhythm.speech_rate,
                "articulation_rate": audio_features.rhythm.articulation_rate,
                "pause_count": audio_features.rhythm.pause_count,
                "pause_durations_ms": audio_features.rhythm.pause_durations_ms,
                "speaking_time_ms": audio_features.rhythm.speaking_time_ms,
                "total_duration_ms": audio_features.rhythm.total_duration_ms
            }
        
        return {
            "prosody": prosody_dict,
            "rhythm": rhythm_dict,
            "duration_seconds": audio_features.duration_seconds
        }

    
    async def validate_audio_only(
        self,
        audio_base64: str
    ) -> tuple[QualityCheck, Audio]:
        """
        Solo valida la calidad del audio (sin procesarlo completamente).
        Útil para feedback rápido en la UI.
        """
        audio = self.audio_loader.load_from_base64(audio_base64, source="user")
        quality_check = self.audio_validator.validate(audio)
        return quality_check, audio
    
    async def get_processing_statistics(self) -> Dict:
        """Obtiene estadísticas de procesamiento"""
        storage_stats = await self.audio_features_repository.get_storage_stats()
        
        return {
            "total_features_stored": storage_stats.get("total_documents", 0),
            "total_storage_mb": storage_stats.get("total_size_mb", 0),
            "avg_processing_time_ms": 0
        }