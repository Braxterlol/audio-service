"""
Attempt - Entidad de dominio que representa un intento de ejercicio.

Los scores de ML Analysis (pronunciation, fluency, rhythm) son opcionales
porque se calculan después del procesamiento inicial.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class AttemptStatus(Enum):
    """Estados posibles de un intento"""
    PENDING_ANALYSIS = "pending_analysis"  # Esperando análisis ML
    COMPLETED = "completed"  # Análisis completado
    QUALITY_REJECTED = "quality_rejected"  # Rechazado por baja calidad


@dataclass
class Attempt:
    """
    Entidad Attempt - Representa un intento de ejercicio por un usuario.
    
    Ciclo de vida:
    1. Se crea con status=PENDING_ANALYSIS después de procesar audio
    2. ML Analysis Service calcula los scores
    3. Se actualiza a status=COMPLETED con los scores finales
    """
    
    # Identificadores
    id: str
    user_id: str
    exercise_id: str
    
    # Timestamps
    attempted_at: datetime
    analyzed_at: Optional[datetime] = None
    
    # Estado
    status: AttemptStatus = AttemptStatus.PENDING_ANALYSIS
    
    # Calidad del audio (se llenan inmediatamente)
    audio_quality_score: Optional[float] = None
    audio_snr_db: Optional[float] = None
    has_background_noise: bool = False
    has_clipping: bool = False
    
    # Métricas acústicas básicas (se llenan inmediatamente)
    total_duration_seconds: Optional[float] = None
    speech_rate: Optional[float] = None  # sílabas/segundo
    articulation_rate: Optional[float] = None  # sílabas/segundo (sin pausas)
    pause_count: Optional[int] = None
    
    # Scores de ML Analysis (se llenan DESPUÉS por ML Analysis Service)
    overall_score: Optional[float] = None
    pronunciation_score: Optional[float] = None
    fluency_score: Optional[float] = None
    rhythm_score: Optional[float] = None
    
    # Análisis de errores (se llena DESPUÉS)
    error_count: int = 0
    
    # Referencias
    features_doc_id: Optional[str] = None  # ID del documento en MongoDB
    
    # Metadata
    processing_time_ms: Optional[int] = None
    
    @staticmethod
    def create_new(
        user_id: str,
        exercise_id: str,
        audio_quality_score: float,
        audio_snr_db: float,
        has_background_noise: bool,
        has_clipping: bool,
        total_duration_seconds: float,
        speech_rate: Optional[float] = None,
        articulation_rate: Optional[float] = None,
        pause_count: Optional[int] = None,
        features_doc_id: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> "Attempt":
        """
        Factory method para crear un nuevo intento.
        
        Los scores de ML Analysis (pronunciation, fluency, rhythm) se dejan en None
        porque serán calculados después por el ML Analysis Service.
        
        Args:
            user_id: ID del usuario
            exercise_id: ID del ejercicio
            audio_quality_score: Score de calidad (0-10)
            audio_snr_db: SNR en dB
            has_background_noise: Si tiene ruido de fondo
            has_clipping: Si tiene clipping
            total_duration_seconds: Duración total
            speech_rate: Tasa de habla (opcional)
            articulation_rate: Tasa de articulación (opcional)
            pause_count: Número de pausas (opcional)
            features_doc_id: ID del documento MongoDB
            processing_time_ms: Tiempo de procesamiento
        
        Returns:
            Attempt: Nueva instancia con status PENDING_ANALYSIS
        """
        return Attempt(
            id=str(uuid.uuid4()),
            user_id=user_id,
            exercise_id=exercise_id,
            attempted_at=datetime.utcnow(),
            status=AttemptStatus.PENDING_ANALYSIS,
            audio_quality_score=audio_quality_score,
            audio_snr_db=audio_snr_db,
            has_background_noise=has_background_noise,
            has_clipping=has_clipping,
            total_duration_seconds=total_duration_seconds,
            speech_rate=speech_rate,
            articulation_rate=articulation_rate,
            pause_count=pause_count,
            features_doc_id=features_doc_id,
            processing_time_ms=processing_time_ms,
            # Scores de ML - inicialmente None
            overall_score=None,
            pronunciation_score=None,
            fluency_score=None,
            rhythm_score=None,
            error_count=0,
            analyzed_at=None
        )
    
    def mark_as_completed(
        self,
        overall_score: float,
        pronunciation_score: float,
        fluency_score: float,
        rhythm_score: float,
        error_count: int = 0
    ):
        """
        Marca el intento como completado después del análisis ML.
        
        Este método será llamado por el ML Analysis Service.
        
        Args:
            overall_score: Score general (0-100)
            pronunciation_score: Score de pronunciación (0-100)
            fluency_score: Score de fluidez (0-100)
            rhythm_score: Score de ritmo (0-100)
            error_count: Cantidad de errores detectados
        """
        self.status = AttemptStatus.COMPLETED
        self.overall_score = overall_score
        self.pronunciation_score = pronunciation_score
        self.fluency_score = fluency_score
        self.rhythm_score = rhythm_score
        self.error_count = error_count
        self.analyzed_at = datetime.utcnow()
    
    def mark_as_rejected(self, reason: str):
        """
        Marca el intento como rechazado por baja calidad.
        
        Args:
            reason: Razón del rechazo
        """
        self.status = AttemptStatus.QUALITY_REJECTED
        self.analyzed_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para respuestas JSON"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "exercise_id": self.exercise_id,
            "attempted_at": self.attempted_at.isoformat(),
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "status": self.status.value,
            "audio_quality": {
                "quality_score": self.audio_quality_score,
                "snr_db": self.audio_snr_db,
                "has_background_noise": self.has_background_noise,
                "has_clipping": self.has_clipping
            },
            "basic_metrics": {
                "duration_seconds": self.total_duration_seconds,
                "speech_rate": self.speech_rate,
                "articulation_rate": self.articulation_rate,
                "pause_count": self.pause_count
            },
            "scores": {
                "overall": self.overall_score,
                "pronunciation": self.pronunciation_score,
                "fluency": self.fluency_score,
                "rhythm": self.rhythm_score
            } if self.overall_score is not None else None,
            "error_count": self.error_count,
            "features_doc_id": self.features_doc_id,
            "processing_time_ms": self.processing_time_ms
        }
    
    def __repr__(self) -> str:
        return (
            f"Attempt(id={self.id[:8]}..., "
            f"user={self.user_id[:8]}..., "
            f"exercise={self.exercise_id}, "
            f"status={self.status.value}, "
            f"overall_score={self.overall_score})"
        )