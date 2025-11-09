"""
ProsodyAnalyzer - Analiza características prosódicas (F0, jitter, shimmer).
"""

import numpy as np
import librosa
import parselmouth
from parselmouth.praat import call
from typing import Dict, Optional
from src.audio_processing.domain.models.audio import Audio


class ProsodyAnalyzer:
    """
    Analizador de prosodia.
    
    Extrae:
    - F0 (frecuencia fundamental / pitch)
    - Jitter (variabilidad del pitch)
    - Shimmer (variabilidad de amplitud)
    - Intensidad
    """
    
    def __init__(
        self,
        f0_min: float = 75.0,   # Hz (típico para voz masculina)
        f0_max: float = 500.0,  # Hz (típico para voz femenina/infantil)
    ):
        """
        Args:
            f0_min: Frecuencia fundamental mínima (Hz)
            f0_max: Frecuencia fundamental máxima (Hz)
        """
        self.f0_min = f0_min
        self.f0_max = f0_max
    
    def extract(self, audio: Audio) -> Dict[str, float]:
        """
        Extrae todas las características prosódicas.
        
        Args:
            audio: Audio del cual extraer características
        
        Returns:
            Dict con características prosódicas
        """
        features = {}
        
        # Extraer F0 (pitch)
        f0_features = self._extract_f0(audio)
        features.update(f0_features)
        
        # Extraer jitter y shimmer usando Praat
        try:
            praat_features = self._extract_praat_features(audio)
            features.update(praat_features)
        except Exception as e:
            # Si falla Praat, usar valores por defecto
            print(f"⚠️ Warning: No se pudo extraer características con Praat: {e}")
            features.update({
                'jitter_local': 0.0,
                'jitter_rap': 0.0,
                'shimmer_local': 0.0,
                'shimmer_apq': 0.0,
                'hnr': 0.0  # Harmonics-to-Noise Ratio
            })
        
        # Extraer intensidad
        intensity_features = self._extract_intensity(audio)
        features.update(intensity_features)
        
        return features
    
    def _extract_f0(self, audio: Audio) -> Dict[str, float]:
        """
        Extrae características de F0 (pitch).
        
        Args:
            audio: Audio
        
        Returns:
            Dict con características de F0
        """
        y = audio.data
        sr = audio.metadata.sample_rate
        
        # Extraer F0 usando librosa (YIN algorithm)
        f0 = librosa.yin(
            y,
            fmin=self.f0_min,
            fmax=self.f0_max,
            sr=sr
        )
        
        # Filtrar valores válidos (> 0)
        f0_valid = f0[f0 > 0]
        
        if len(f0_valid) == 0:
            return {
                'f0_mean': 0.0,
                'f0_std': 0.0,
                'f0_min': 0.0,
                'f0_max': 0.0,
                'f0_range': 0.0,
                'f0_median': 0.0,
                'f0_iqr': 0.0,  # Interquartile range
                'voicing_rate': 0.0  # % de frames con voz
            }
        
        # Calcular estadísticas
        f0_mean = float(np.mean(f0_valid))
        f0_std = float(np.std(f0_valid))
        f0_min = float(np.min(f0_valid))
        f0_max = float(np.max(f0_valid))
        f0_range = f0_max - f0_min
        f0_median = float(np.median(f0_valid))
        
        # Calcular IQR (rango intercuartílico)
        q75, q25 = np.percentile(f0_valid, [75, 25])
        f0_iqr = float(q75 - q25)
        
        # Calcular tasa de voicing (% de frames con F0 válido)
        voicing_rate = float(len(f0_valid) / len(f0))
        
        return {
            'f0_mean': f0_mean,
            'f0_std': f0_std,
            'f0_min': f0_min,
            'f0_max': f0_max,
            'f0_range': f0_range,
            'f0_median': f0_median,
            'f0_iqr': f0_iqr,
            'voicing_rate': voicing_rate
        }
    
    def _extract_praat_features(self, audio: Audio) -> Dict[str, float]:
        """
        Extrae jitter, shimmer y HNR usando Praat/Parselmouth.
        
        Args:
            audio: Audio
        
        Returns:
            Dict con características de Praat
        """
        y = audio.data
        sr = audio.metadata.sample_rate
        
        # Crear objeto Sound de Parselmouth
        sound = parselmouth.Sound(y, sampling_frequency=sr)
        
        # Extraer pitch
        pitch = call(sound, "To Pitch", 0.0, self.f0_min, self.f0_max)
        
        # Extraer point process para jitter/shimmer
        point_process = call(
            sound,
            "To PointProcess (periodic, cc)",
            self.f0_min,
            self.f0_max
        )
        
        # Jitter (variabilidad del periodo)
        try:
            jitter_local = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
            jitter_rap = call(point_process, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
        except:
            jitter_local = 0.0
            jitter_rap = 0.0
        
        # Shimmer (variabilidad de amplitud)
        try:
            shimmer_local = call(
                [sound, point_process],
                "Get shimmer (local)",
                0, 0, 0.0001, 0.02, 1.3, 1.6
            )
            shimmer_apq = call(
                [sound, point_process],
                "Get shimmer (apq3)",
                0, 0, 0.0001, 0.02, 1.3, 1.6
            )
        except:
            shimmer_local = 0.0
            shimmer_apq = 0.0
        
        # HNR (Harmonics-to-Noise Ratio)
        try:
            harmonicity = call(sound, "To Harmonicity (cc)", 0.01, self.f0_min, 0.1, 1.0)
            hnr = call(harmonicity, "Get mean", 0, 0)
        except:
            hnr = 0.0
        
        return {
            'jitter_local': float(jitter_local) if not np.isnan(jitter_local) else 0.0,
            'jitter_rap': float(jitter_rap) if not np.isnan(jitter_rap) else 0.0,
            'shimmer_local': float(shimmer_local) if not np.isnan(shimmer_local) else 0.0,
            'shimmer_apq': float(shimmer_apq) if not np.isnan(shimmer_apq) else 0.0,
            'hnr': float(hnr) if not np.isnan(hnr) else 0.0
        }
    
    def _extract_intensity(self, audio: Audio) -> Dict[str, float]:
        """
        Extrae características de intensidad (volumen).
        
        Args:
            audio: Audio
        
        Returns:
            Dict con características de intensidad
        """
        y = audio.data
        sr = audio.metadata.sample_rate
        
        # Calcular RMS energy
        rms = librosa.feature.rms(y=y)[0]
        
        # Convertir a dB
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        
        # Estadísticas
        intensity_mean = float(np.mean(rms_db))
        intensity_std = float(np.std(rms_db))
        intensity_min = float(np.min(rms_db))
        intensity_max = float(np.max(rms_db))
        intensity_range = intensity_max - intensity_min
        
        return {
            'intensity_mean': intensity_mean,
            'intensity_std': intensity_std,
            'intensity_min': intensity_min,
            'intensity_max': intensity_max,
            'intensity_range': intensity_range
        }
    
    def compare_prosody(
        self,
        audio1: Audio,
        audio2: Audio
    ) -> Dict[str, float]:
        """
        Compara características prosódicas entre dos audios.
        
        Args:
            audio1: Audio del usuario
            audio2: Audio de referencia
        
        Returns:
            Dict con scores de similitud
        """
        features1 = self.extract(audio1)
        features2 = self.extract(audio2)
        
        # Comparar F0 (pitch)
        f0_diff = abs(features1['f0_mean'] - features2['f0_mean'])
        f0_similarity = max(0, 100 - (f0_diff / features2['f0_mean']) * 100)
        
        # Comparar variabilidad de F0
        f0_std_diff = abs(features1['f0_std'] - features2['f0_std'])
        f0_std_similarity = max(0, 100 - (f0_std_diff / (features2['f0_std'] + 1)) * 100)
        
        # Comparar intensidad
        intensity_diff = abs(features1['intensity_mean'] - features2['intensity_mean'])
        intensity_similarity = max(0, 100 - intensity_diff * 2)
        
        return {
            'f0_similarity': float(f0_similarity),
            'f0_std_similarity': float(f0_std_similarity),
            'intensity_similarity': float(intensity_similarity),
            'prosody_overall_similarity': float(
                (f0_similarity * 0.5 + f0_std_similarity * 0.3 + intensity_similarity * 0.2)
            )
        }

