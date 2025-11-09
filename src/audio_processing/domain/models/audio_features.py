"""
Value Object AudioFeatures - Features acústicos extraídos de un audio.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import numpy as np


@dataclass(frozen=True)
class MFCCFeatures:
    """Features MFCCs"""
    coefficients: List[List[float]]  # [13 x frames]
    delta: List[List[float]]
    delta_delta: List[List[float]]
    stats: Dict[str, List[float]]  # mean, std, min, max


@dataclass(frozen=True)
class ProsodyFeatures:
    """Features prosódicos"""
    f0_curve: List[float]
    f0_stats: Dict[str, float]  # mean, std, min, max, median, range
    jitter: float
    shimmer: float
    energy_contour: List[float]
    energy_stats: Dict[str, float]


@dataclass(frozen=True)
class PhonemeSegment:
    """Segmento fonético"""
    phoneme: str
    start_time: float
    end_time: float
    duration_ms: int
    formant_f1: float
    formant_f2: float
    formant_f3: float
    position_in_word: str  # 'inicial', 'media', 'final'


@dataclass(frozen=True)
class RhythmFeatures:
    """Features de ritmo"""
    speech_rate: float  # sílabas/segundo
    articulation_rate: float  # sílabas/segundo sin pausas
    pause_count: int
    pause_durations_ms: List[int]
    total_pause_time_ms: int
    speaking_time_ms: int
    total_duration_ms: int


@dataclass(frozen=True)
class AudioFeatures:
    """
    Value Object que encapsula todas las features extraídas de un audio.
    
    Este objeto es inmutable y representa un snapshot completo
    de las características acústicas de un audio.
    """
    
    # Identificadores
    attempt_id: str  # UUID del intento
    exercise_id: str
    user_id: str
    
    # Features principales
    mfcc: MFCCFeatures
    prosody: ProsodyFeatures
    rhythm: RhythmFeatures
    phoneme_segments: List[PhonemeSegment] = field(default_factory=list)
    
    # Metadata
    duration_seconds: float = 0.0
    phoneme_count: int = 0
    processing_version: str = "v1.0"
    
    def __post_init__(self):
        """Validaciones"""
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds debe ser mayor a 0")
        
        if len(self.mfcc.coefficients) == 0:
            raise ValueError("MFCCs no pueden estar vacíos")
    
    def get_mfcc_mean(self) -> List[float]:
        """Obtiene la media de los MFCCs"""
        return self.mfcc.stats.get('mean', [])
    
    def get_mfcc_std(self) -> List[float]:
        """Obtiene la desviación estándar de los MFCCs"""
        return self.mfcc.stats.get('std', [])
    
    def get_f0_mean(self) -> float:
        """Obtiene la media de F0"""
        return self.prosody.f0_stats.get('mean', 0.0)
    
    def get_f0_range(self) -> float:
        """Obtiene el rango de F0"""
        return self.prosody.f0_stats.get('range', 0.0)
    
    def has_phoneme_segments(self) -> bool:
        """Verifica si tiene segmentación fonética"""
        return len(self.phoneme_segments) > 0
    
    def get_phoneme_by_type(self, phoneme: str) -> List[PhonemeSegment]:
        """Obtiene todos los segmentos de un fonema específico"""
        return [seg for seg in self.phoneme_segments if seg.phoneme == phoneme]
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para MongoDB"""
        return {
            "attempt_id": self.attempt_id,
            "exercise_id": self.exercise_id,
            "user_id": self.user_id,
            "mfcc": {
                "coefficients": self.mfcc.coefficients,
                "delta": self.mfcc.delta,
                "delta_delta": self.mfcc.delta_delta,
                "stats": self.mfcc.stats
            },
            "prosody": {
                "f0_curve": self.prosody.f0_curve,
                "f0_stats": self.prosody.f0_stats,
                "jitter": self.prosody.jitter,
                "shimmer": self.prosody.shimmer,
                "energy_contour": self.prosody.energy_contour,
                "energy_stats": self.prosody.energy_stats
            },
            "rhythm": {
                "speech_rate": self.rhythm.speech_rate,
                "articulation_rate": self.rhythm.articulation_rate,
                "pause_count": self.rhythm.pause_count,
                "pause_durations_ms": self.rhythm.pause_durations_ms,
                "total_pause_time_ms": self.rhythm.total_pause_time_ms,
                "speaking_time_ms": self.rhythm.speaking_time_ms,
                "total_duration_ms": self.rhythm.total_duration_ms
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
            "processing_version": self.processing_version
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AudioFeatures':
        """Crea instancia desde diccionario (MongoDB)"""
        return cls(
            attempt_id=data['attempt_id'],
            exercise_id=data['exercise_id'],
            user_id=data['user_id'],
            mfcc=MFCCFeatures(
                coefficients=data['mfcc']['coefficients'],
                delta=data['mfcc']['delta'],
                delta_delta=data['mfcc']['delta_delta'],
                stats=data['mfcc']['stats']
            ),
            prosody=ProsodyFeatures(
                f0_curve=data['prosody']['f0_curve'],
                f0_stats=data['prosody']['f0_stats'],
                jitter=data['prosody']['jitter'],
                shimmer=data['prosody']['shimmer'],
                energy_contour=data['prosody']['energy_contour'],
                energy_stats=data['prosody']['energy_stats']
            ),
            rhythm=RhythmFeatures(
                speech_rate=data['rhythm']['speech_rate'],
                articulation_rate=data['rhythm']['articulation_rate'],
                pause_count=data['rhythm']['pause_count'],
                pause_durations_ms=data['rhythm']['pause_durations_ms'],
                total_pause_time_ms=data['rhythm']['total_pause_time_ms'],
                speaking_time_ms=data['rhythm']['speaking_time_ms'],
                total_duration_ms=data['rhythm']['total_duration_ms']
            ),
            phoneme_segments=[
                PhonemeSegment(**seg) for seg in data.get('phoneme_segments', [])
            ],
            duration_seconds=data['duration_seconds'],
            phoneme_count=data.get('phoneme_count', 0),
            processing_version=data.get('processing_version', 'v1.0')
        )
    
    def __repr__(self) -> str:
        return (
            f"AudioFeatures(attempt_id={self.attempt_id[:8]}..., "
            f"duration={self.duration_seconds:.2f}s, "
            f"segments={len(self.phoneme_segments)})"
        )