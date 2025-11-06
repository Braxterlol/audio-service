from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass(frozen=True)  # frozen=True lo hace inmutable
class ProsodyStats:
    """Estadísticas de prosodia (F0, jitter, shimmer)"""
    f0_mean: float
    f0_std: float
    f0_min: float
    f0_max: float
    f0_median: float
    f0_range: float
    jitter: float
    shimmer: float


@dataclass(frozen=True)
class MFCCStats:
    """Estadísticas de MFCCs"""
    mean: List[float]  # 13 valores
    std: List[float]   # 13 valores
    min: List[float]   # 13 valores
    max: List[float]   # 13 valores


@dataclass(frozen=True)
class PhonemeSegment:
    """Segmento fonético del audio de referencia"""
    phoneme: str
    start_time: float
    end_time: float
    duration_ms: int
    formant_f1: float
    formant_f2: float
    formant_f3: float
    position_in_word: str  # 'inicial', 'media', 'final'


@dataclass(frozen=True)
class NormalizationParams:
    """Parámetros de normalización para comparación"""
    mfcc_mean: List[float]
    mfcc_std: List[float]
    f0_range: tuple[float, float]  # (min, max)
    energy_range: tuple[float, float]


@dataclass(frozen=True)
class ComparisonThresholds:
    """Umbrales para comparación DTW"""
    dtw_good: float = 0.15        # < 0.15 = buena pronunciación
    dtw_acceptable: float = 0.30  # < 0.30 = aceptable
    dtw_poor: float = 0.50        # > 0.50 = necesita práctica
    phoneme_duration_tolerance: float = 0.20  # ±20%
    f0_tolerance: float = 0.15                # ±15%


@dataclass(frozen=True)
class ReferenceFeatures:
    """
    Value Object que encapsula todas las características del audio de referencia.
    
    Este objeto es inmutable (frozen=True) porque representa un snapshot
    de las features calculadas que no deberían cambiar.
    
    Attributes:
        exercise_id: ID del ejercicio al que pertenecen estas features
        mfcc_stats: Estadísticas de MFCCs
        prosody_stats: Estadísticas prosódicas
        phoneme_segments: Lista de segmentos fonéticos
        duration_seconds: Duración total del audio
        phoneme_count: Número de fonemas
        normalization_params: Parámetros para normalización
        thresholds: Umbrales de comparación
        cache_version: Versión del caché
        cached_at: Fecha de precálculo
    """
    
    exercise_id: str
    
    # Features principales
    mfcc_stats: MFCCStats
    prosody_stats: ProsodyStats
    
    # Metadata
    duration_seconds: float
    phoneme_count: int
    
    # Parámetros de comparación
    normalization_params: NormalizationParams
    
    # Listas con valores por defecto
    phoneme_segments: List[PhonemeSegment] = field(default_factory=list)
    thresholds: ComparisonThresholds = field(default_factory=ComparisonThresholds)
    
    # Caché info
    cache_version: str = "v1.0"
    cached_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validaciones del value object"""
        if self.duration_seconds <= 0:
            raise ValueError("La duración debe ser mayor a 0")
        
        if self.phoneme_count < 0:
            raise ValueError("El conteo de fonemas no puede ser negativo")
        
        if len(self.mfcc_stats.mean) != 13:
            raise ValueError("MFCCs deben tener 13 coeficientes")
    
    # ========================================
    # MÉTODOS DE CONSULTA (Query Methods)
    # ========================================
    
    def get_phoneme_segments_by_type(self, phoneme: str) -> List[PhonemeSegment]:
        """
        Obtiene todos los segmentos de un fonema específico.
        
        Args:
            phoneme: Fonema a buscar (ej: "/r/")
        
        Returns:
            List[PhonemeSegment]: Lista de segmentos encontrados
        """
        return [seg for seg in self.phoneme_segments if seg.phoneme == phoneme]
    
    def get_average_phoneme_duration(self, phoneme: str) -> Optional[float]:
        """
        Calcula la duración promedio de un fonema en el audio de referencia.
        
        Args:
            phoneme: Fonema a analizar
        
        Returns:
            float: Duración promedio en milisegundos, o None si no existe
        """
        segments = self.get_phoneme_segments_by_type(phoneme)
        if not segments:
            return None
        
        total_duration = sum(seg.duration_ms for seg in segments)
        return total_duration / len(segments)
    
    def get_f0_range_normalized(self) -> tuple[float, float]:
        """
        Retorna el rango de F0 para normalización.
        
        Returns:
            tuple: (f0_min, f0_max)
        """
        return self.normalization_params.f0_range
    
    def is_within_expected_duration(self, user_duration: float) -> bool:
        """
        Verifica si la duración del usuario está dentro del rango esperado.
        
        Args:
            user_duration: Duración en segundos del audio del usuario
        
        Returns:
            bool: True si está dentro del rango aceptable (±30%)
        """
        tolerance = 0.30  # 30%
        min_duration = self.duration_seconds * (1 - tolerance)
        max_duration = self.duration_seconds * (1 + tolerance)
        
        return min_duration <= user_duration <= max_duration
    
    def classify_dtw_distance(self, dtw_normalized: float) -> str:
        """
        Clasifica una distancia DTW según los umbrales.
        
        Args:
            dtw_normalized: Distancia DTW normalizada (0-1)
        
        Returns:
            str: 'excelente', 'buena', 'aceptable' o 'necesita_practica'
        """
        if dtw_normalized < self.thresholds.dtw_good:
            return 'excelente'
        elif dtw_normalized < self.thresholds.dtw_acceptable:
            return 'buena'
        elif dtw_normalized < self.thresholds.dtw_poor:
            return 'aceptable'
        else:
            return 'necesita_practica'
    
    def to_dict(self) -> dict:
        """Convierte el value object a diccionario"""
        return {
            "exercise_id": self.exercise_id,
            "mfcc_stats": {
                "mean": self.mfcc_stats.mean,
                "std": self.mfcc_stats.std,
                "min": self.mfcc_stats.min,
                "max": self.mfcc_stats.max
            },
            "prosody_stats": {
                "f0_mean": self.prosody_stats.f0_mean,
                "f0_std": self.prosody_stats.f0_std,
                "f0_min": self.prosody_stats.f0_min,
                "f0_max": self.prosody_stats.f0_max,
                "f0_median": self.prosody_stats.f0_median,
                "f0_range": self.prosody_stats.f0_range,
                "jitter": self.prosody_stats.jitter,
                "shimmer": self.prosody_stats.shimmer
            },
            "phoneme_segments": [
                {
                    "phoneme": seg.phoneme,
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "duration_ms": seg.duration_ms,
                    "formant_f1": seg.formant_f1,
                    "formant_f2": seg.formant_f2,
                    "formant_f3": seg.formant_f3,
                    "position_in_word": seg.position_in_word
                }
                for seg in self.phoneme_segments
            ],
            "duration_seconds": self.duration_seconds,
            "phoneme_count": self.phoneme_count,
            "normalization_params": {
                "mfcc_mean": self.normalization_params.mfcc_mean,
                "mfcc_std": self.normalization_params.mfcc_std,
                "f0_range": list(self.normalization_params.f0_range),
                "energy_range": list(self.normalization_params.energy_range)
            },
            "thresholds": {
                "dtw_good": self.thresholds.dtw_good,
                "dtw_acceptable": self.thresholds.dtw_acceptable,
                "dtw_poor": self.thresholds.dtw_poor,
                "phoneme_duration_tolerance": self.thresholds.phoneme_duration_tolerance,
                "f0_tolerance": self.thresholds.f0_tolerance
            },
            "cache_version": self.cache_version,
            "cached_at": self.cached_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReferenceFeatures':
        """Crea instancia desde diccionario"""
        mfcc_data = data['mfcc_stats']
        prosody_data = data['prosody_stats']
        
        return cls(
            exercise_id=data['exercise_id'],
            mfcc_stats=MFCCStats(
                mean=mfcc_data['mean'],
                std=mfcc_data['std'],
                min=mfcc_data['min'],
                max=mfcc_data['max']
            ),
            prosody_stats=ProsodyStats(
                f0_mean=prosody_data['f0_mean'],
                f0_std=prosody_data['f0_std'],
                f0_min=prosody_data['f0_min'],
                f0_max=prosody_data['f0_max'],
                f0_median=prosody_data['f0_median'],
                f0_range=prosody_data['f0_range'],
                jitter=prosody_data['jitter'],
                shimmer=prosody_data['shimmer']
            ),
            phoneme_segments=[
                PhonemeSegment(**seg) for seg in data.get('phoneme_segments', [])
            ],
            duration_seconds=data['duration_seconds'],
            phoneme_count=data['phoneme_count'],
            normalization_params=NormalizationParams(
                mfcc_mean=data['normalization_params']['mfcc_mean'],
                mfcc_std=data['normalization_params']['mfcc_std'],
                f0_range=tuple(data['normalization_params']['f0_range']),
                energy_range=tuple(data['normalization_params']['energy_range'])
            ),
            thresholds=ComparisonThresholds(**data.get('thresholds', {})),
            cache_version=data.get('cache_version', 'v1.0'),
            cached_at=datetime.fromisoformat(data['cached_at']) 
                       if isinstance(data.get('cached_at'), str) 
                       else data.get('cached_at', datetime.utcnow())
        )
    
    def __repr__(self) -> str:
        return f"ReferenceFeatures(exercise_id={self.exercise_id}, duration={self.duration_seconds}s)"

