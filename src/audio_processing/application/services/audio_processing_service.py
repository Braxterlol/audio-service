"""
AudioProcessingService - Servicio de aplicación para procesamiento de audio.

SOLUCIÓN: Usa dataclasses.replace() con los campos correctos de AudioFeatures.
"""

from typing import Dict
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
        feature_extractor: FeatureExtractor = None
    ):
        self.attempt_repository = attempt_repository
        self.audio_features_repository = audio_features_repository
        
        # Helpers
        self.audio_loader = audio_loader or AudioLoader()
        self.audio_validator = audio_validator or AudioValidator()
        self.audio_normalizer = audio_normalizer or AudioNormalizer()
        self.feature_extractor = feature_extractor or FeatureExtractor()
    
    async def process_audio_complete(
        self,
        audio_base64: str,
        user_id: str,
        exercise_id: str
    ) -> tuple[Attempt, AudioFeatures, QualityCheck]:
        """
        Procesa un audio completo.
        
        FLUJO:
        1. Cargar y validar audio
        2. Si es inválido, guardar attempt rechazado y lanzar error
        3. Normalizar audio
        4. Extraer features RAW (con attempt_id temporal)
        5. Crear y guardar Attempt en Postgres → obtener ID
        6. Actualizar AudioFeatures con attempt_id correcto usando replace()
        7. Guardar AudioFeatures en MongoDB
        """
        start_time = datetime.utcnow()
        
        # 1. Cargar audio
        audio = self.audio_loader.load_from_base64(audio_base64, source="user")
        
        # 2. Validar calidad
        quality_check = self.audio_validator.validate(audio)
        
        if not quality_check.is_valid:
            # Crear intento fallido (Postgres generará el ID)
            attempt = Attempt(
                id=None,
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
        
        # 4. Extraer features RAW (con attempt_id temporal)
        # El FeatureExtractor debe aceptar attempt_id="temp"
        features_raw = self.feature_extractor.extract_all_features(
            audio_normalized,
            attempt_id="temp",  # Temporal, lo reemplazaremos
            exercise_id=exercise_id,
            user_id=user_id
        )
        
        # 5. Calcular tiempo de procesamiento
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # 6. Crear Attempt (Postgres generará el ID)
        attempt = Attempt(
            id=None,
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
            features_doc_id=None,  # Lo setearemos después
            processing_time_ms=processing_time,
            status=AttemptStatus.PENDING_ANALYSIS
        )
        
        # 7. Guardar Attempt en PostgreSQL → Postgres genera el ID y lo retorna
        attempt = await self.attempt_repository.save(attempt)
        
        # 8. ✅ Actualizar AudioFeatures con attempt_id correcto usando replace()
        # Como AudioFeatures es frozen, usamos replace() de dataclasses
        audio_features = replace(features_raw, attempt_id=attempt.id)
        
        # 9. Guardar features en MongoDB usando el ID de Postgres
        await self.audio_features_repository.save(audio_features)
        
        # 10. Actualizar el features_doc_id en el attempt
        attempt.features_doc_id = attempt.id  # Usamos el mismo ID
        await self.attempt_repository.save(attempt)
        
        return attempt, audio_features, quality_check
    
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