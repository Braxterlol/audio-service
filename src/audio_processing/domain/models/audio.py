"""
Value Object Audio - Representa audio crudo antes de procesarse.

Este es un Value Object inmutable que representa el audio
en diferentes formatos durante el procesamiento.
"""

from dataclasses import dataclass
from typing import Optional
import base64
import numpy as np


@dataclass(frozen=True)
class AudioMetadata:
    """Metadata del audio"""
    sample_rate: int
    duration_seconds: float
    channels: int
    bit_depth: Optional[int] = None
    format: str = "wav"


@dataclass(frozen=True)
class Audio:
    """
    Value Object que representa un audio.
    
    Attributes:
        data: Audio como numpy array
        metadata: Información del audio
        source: Origen del audio ('user', 'reference')
    """
    
    data: np.ndarray  # Audio signal como array numpy
    metadata: AudioMetadata
    source: str = "user"  # 'user' o 'reference'
    
    def __post_init__(self):
        """Validaciones"""
        if len(self.data) == 0:
            raise ValueError("Audio data no puede estar vacío")
        
        if self.metadata.duration_seconds <= 0:
            raise ValueError("Duración debe ser mayor a 0")
        
        if self.source not in ['user', 'reference']:
            raise ValueError("Source debe ser 'user' o 'reference'")
    
    @property
    def duration_ms(self) -> float:
        """Duración en milisegundos"""
        return self.metadata.duration_seconds * 1000
    
    @property
    def sample_count(self) -> int:
        """Número de muestras"""
        return len(self.data)
    
    def is_mono(self) -> bool:
        """Verifica si es mono"""
        return self.metadata.channels == 1
    
    def is_stereo(self) -> bool:
        """Verifica si es estéreo"""
        return self.metadata.channels == 2
    
    def to_dict(self) -> dict:
        """Convierte a diccionario (sin el array de audio)"""
        return {
            "metadata": {
                "sample_rate": self.metadata.sample_rate,
                "duration_seconds": self.metadata.duration_seconds,
                "channels": self.metadata.channels,
                "bit_depth": self.metadata.bit_depth,
                "format": self.metadata.format
            },
            "source": self.source,
            "sample_count": self.sample_count
        }
    
    @classmethod
    def from_base64(cls, base64_data: str, source: str = "user") -> 'Audio':
        """
        Crea instancia desde base64.
        La conversión real se hará en infrastructure/helpers/audio_loader.py
        
        Args:
            base64_data: Audio en base64
            source: Origen del audio
        
        Returns:
            Audio: Instancia de Audio
        """
        # Este método es un placeholder
        # La implementación real estará en audio_loader.py
        raise NotImplementedError(
            "Use audio_loader.AudioLoader.load_from_base64() instead"
        )
    
    def __repr__(self) -> str:
        return (
            f"Audio(duration={self.metadata.duration_seconds:.2f}s, "
            f"sr={self.metadata.sample_rate}Hz, "
            f"channels={self.metadata.channels}, "
            f"source={self.source})"
        )