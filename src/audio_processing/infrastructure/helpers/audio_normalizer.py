"""
AudioNormalizer - Normaliza y preprocesa audio.
"""

import numpy as np
import librosa
import noisereduce as nr
from src.audio_processing.domain.models.audio import Audio, AudioMetadata


class AudioNormalizer:
    """
    Normalizador de audio.
    
    Realiza:
    - Normalización de volumen
    - Reducción de ruido
    - Trim de silencios
    """
    
    def __init__(self, target_sample_rate: int = 16000):
        """
        Args:
            target_sample_rate: Frecuencia de muestreo objetivo
        """
        self.target_sample_rate = target_sample_rate
    
    def normalize(
        self,
        audio: Audio,
        reduce_noise: bool = True,
        trim_silence: bool = True,
        normalize_volume: bool = True
    ) -> Audio:
        """
        Normaliza el audio completo.
        
        Args:
            audio: Audio original
            reduce_noise: Si aplicar reducción de ruido
            trim_silence: Si recortar silencios
            normalize_volume: Si normalizar volumen
        
        Returns:
            Audio: Audio normalizado
        """
        y = audio.data.copy()
        sr = audio.metadata.sample_rate
        
        # 1. Reducir ruido (si está habilitado)
        if reduce_noise:
            y = self._reduce_noise(y, sr)
        
        # 2. Trim silencios del inicio/fin
        if trim_silence:
            y = self._trim_silence(y)
        
        # 3. Normalizar volumen
        if normalize_volume:
            y = self._normalize_volume(y)
        
        # 4. Calcular nueva duración
        duration = len(y) / sr
        
        # Crear nueva metadata
        new_metadata = AudioMetadata(
            sample_rate=sr,
            duration_seconds=float(duration),
            channels=audio.metadata.channels,
            format=audio.metadata.format
        )
        
        return Audio(
            data=y,
            metadata=new_metadata,
            source=audio.source
        )
    
    def _reduce_noise(self, y: np.ndarray, sr: int) -> np.ndarray:
        """
        Reduce ruido de fondo.
        
        Args:
            y: Audio signal
            sr: Sample rate
        
        Returns:
            np.ndarray: Audio con ruido reducido
        """
        try:
            # Usar noisereduce
            y_clean = nr.reduce_noise(y=y, sr=sr)
            return y_clean
        except Exception as e:
            print(f"⚠️ Warning: No se pudo reducir ruido: {e}")
            return y
    
    def _trim_silence(
        self,
        y: np.ndarray,
        top_db: float = 20.0
    ) -> np.ndarray:
        """
        Recorta silencios del inicio y final.
        
        Args:
            y: Audio signal
            top_db: Threshold en dB para considerar silencio
        
        Returns:
            np.ndarray: Audio trimmed
        """
        y_trimmed, _ = librosa.effects.trim(y, top_db=top_db)
        
        # Asegurar que no quedó vacío
        if len(y_trimmed) < 100:
            return y
        
        return y_trimmed
    
    def _normalize_volume(
        self,
        y: np.ndarray,
        target_level: float = 0.7
    ) -> np.ndarray:
        """
        Normaliza el volumen del audio.
        
        Args:
            y: Audio signal
            target_level: Nivel objetivo (0-1)
        
        Returns:
            np.ndarray: Audio normalizado
        """
        # Calcular nivel actual
        current_level = np.max(np.abs(y))
        
        if current_level < 1e-10:  # Audio silencioso
            return y
        
        # Normalizar
        y_normalized = y * (target_level / current_level)
        
        # Asegurar que no excede [-1, 1]
        y_normalized = np.clip(y_normalized, -1.0, 1.0)
        
        return y_normalized
    
    def resample(self, audio: Audio, target_sr: int) -> Audio:
        """
        Resample audio a diferente frecuencia.
        
        Args:
            audio: Audio original
            target_sr: Frecuencia objetivo
        
        Returns:
            Audio: Audio resampleado
        """
        if audio.metadata.sample_rate == target_sr:
            return audio
        
        y_resampled = librosa.resample(
            audio.data,
            orig_sr=audio.metadata.sample_rate,
            target_sr=target_sr
        )
        
        duration = len(y_resampled) / target_sr
        
        new_metadata = AudioMetadata(
            sample_rate=target_sr,
            duration_seconds=float(duration),
            channels=audio.metadata.channels,
            format=audio.metadata.format
        )
        
        return Audio(
            data=y_resampled,
            metadata=new_metadata,
            source=audio.source
        )
