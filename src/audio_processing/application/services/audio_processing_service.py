"""
AudioProcessingService - Servicio de aplicación para procesamiento de audio.

Coordina operaciones complejas que involucran múltiples helpers y repositorios.
"""

from typing import Optional, Dict
from datetime import datetime
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
    
    Orquesta el flujo completo:
    1. Cargar audio
    2. Validar calidad
    3. Normalizar
    4. Extraer features
    5. Guardar en repositorios
    """
    
    def __init__(
        self,
        attempt_repository: AttemptRepository,
        audio_features_repository: AudioFeaturesRepository,
        audio_loader: Optional[AudioLoader] = None,
        audio_validator: Optional[AudioValidator] = None,
        audio_normalizer: Optional[AudioNormalizer] = None,
        feature_extractor: Optional[FeatureExtractor] = None
    ):
        """
        Args:
            attempt_repository: Repositorio de intentos
            audio_features_repository: Repositorio de features
            audio_loader: Cargador de audio (opcional, se crea si no se provee)
            audio_validator: Validador (opcional)
            audio_normalizer: Normalizador (opcional)
            feature_extractor: Extractor de features (opcional)
        """
        self.attempt_repository = attempt_repository
        self.audio_features_repository = audio_features_repository
        
        # Helpers (crear instancias por defecto si no se proveen)
        self.audio_loader = audio_loader or AudioLoader()
        self.audio_validator = audio_validator or AudioValidator()
        self.audio_normalizer = audio_normalizer or AudioNormalizer()
        self.feature_extractor = feature_extractor or FeatureExtractor()
    
    async def process_audio_complete(
        self,
        audio_base64: str,
        user_id: str,
        exercise_id: str,
        attempt_id: str
    ) -> tuple[Attempt, AudioFeatures, QualityCheck]:
        """
        Procesa un audio completo: carga, valida, normaliza, extrae features.
        
        Args:
            audio_base64: Audio en base64
            user_id: UUID del usuario
            exercise_id: ID del ejercicio
            attempt_id: UUID del intento (ya generado)
        
        Returns:
            tuple: (Attempt, AudioFeatures, QualityCheck)
        
        Raises:
            ValueError: Si el audio es inválido
        """
        start_time = datetime.utcnow()
        
        # 1. Cargar audio
        audio = self.audio_loader.load_from_base64(audio_base64, source="user")
        
        # 2. Validar calidad
        quality_check = self.audio_validator.validate(audio)
        
        if not quality_check.is_valid:
            # Crear intento fallido
            attempt = Attempt(
                id=attempt_id,
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
            attempt.mark_as_quality_rejected(quality_check.rejection_reason)
            
            # Guardar intento fallido
            await self.attempt_repository.save(attempt)
            
            raise ValueError(quality_check.rejection_reason)
        
        # 3. Normalizar audio
        audio_normalized = self.audio_normalizer.normalize(
            audio,
            reduce_noise=True,
            trim_silence=True,
            normalize_volume=True
        )
        
        # 4. Extraer features
        audio_features = self.feature_extractor.extract_all_features(
            audio_normalized,
            attempt_id=attempt_id,
            exercise_id=exercise_id,
            user_id=user_id
        )
        
        # 5. Guardar features en MongoDB
        await self.audio_features_repository.save(audio_features)
        
        # 6. Crear intento (sin scores todavía, los calculará ML Analysis)
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        attempt = Attempt(
            id=attempt_id,
            user_id=user_id,
            exercise_id=exercise_id,
            attempted_at=start_time,
            audio_quality_score=quality_check.quality_score,
            audio_snr_db=quality_check.snr_db,
            has_background_noise=quality_check.has_background_noise,
            has_clipping=quality_check.has_clipping,
            total_duration_seconds=audio_features.duration_seconds,
            speech_rate=audio_features.rhythm.speech_rate,
            articulation_rate=audio_features.rhythm.articulation_rate,
            pause_count=audio_features.rhythm.pause_count,
            features_doc_id=attempt_id,  # Mismo ID que en MongoDB
            processing_time_ms=processing_time,
            status=AttemptStatus.COMPLETED
        )
        
        # 7. Guardar intento en PostgreSQL
        await self.attempt_repository.save(attempt)
        
        return attempt, audio_features, quality_check
    
    async def validate_audio_only(
        self,
        audio_base64: str
    ) -> tuple[QualityCheck, Audio]:
        """
        Solo valida la calidad del audio (sin procesarlo completamente).
        Útil para feedback rápido en la UI.
        
        Args:
            audio_base64: Audio en base64
        
        Returns:
            tuple: (QualityCheck, Audio)
        """
        # Cargar audio
        audio = self.audio_loader.load_from_base64(audio_base64, source="user")
        
        # Validar calidad
        quality_check = self.audio_validator.validate(audio)
        
        return quality_check, audio
    
    async def reprocess_attempt(
        self,
        attempt_id: str
    ) -> AudioFeatures:
        """
        Reprocesa un intento existente (útil si se mejoran los algoritmos).
        
        Args:
            attempt_id: UUID del intento
        
        Returns:
            AudioFeatures: Nuevas features calculadas
        
        Raises:
            ValueError: Si el intento no existe o no tiene audio
        """
        # Obtener intento
        attempt = await self.attempt_repository.find_by_id(attempt_id)
        if not attempt:
            raise ValueError(f"Intento {attempt_id} no encontrado")
        
        # Obtener features originales (que tienen el audio raw si lo guardamos)
        # NOTA: Como NO guardamos el audio raw, esto NO es posible
        # Esta función es un placeholder para el futuro
        
        raise NotImplementedError(
            "Reprocesar intentos requiere guardar el audio original, "
            "lo cual no hacemos por privacidad"
        )
    
    async def get_processing_statistics(self) -> Dict:
        """
        Obtiene estadísticas de procesamiento.
        
        Returns:
            Dict: Estadísticas agregadas
        """
        # Obtener stats de MongoDB
        storage_stats = await self.audio_features_repository.get_storage_stats()
        
        return {
            "total_features_stored": storage_stats.get("total_documents", 0),
            "total_storage_mb": storage_stats.get("total_size_mb", 0),
            "avg_processing_time_ms": 0  # TODO: calcular desde attempts
        }