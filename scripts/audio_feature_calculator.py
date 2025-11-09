"""
AudioFeatureCalculator - Extrae features acústicos de audios de referencia.

Este módulo calcula:
- MFCCs (13 coeficientes + deltas)
- F0, Jitter, Shimmer (prosodia)
- Segmentación básica de fonemas (simplificada sin Forced Aligner)
- Parámetros de normalización
"""

import librosa
import numpy as np
import parselmouth
from parselmouth.praat import call
from typing import Dict, List, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')


class AudioFeatureCalculator:
    """
    Calculador de features acústicos para audios de referencia.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        n_mfcc: int = 13,
        hop_length: int = 512,
        n_fft: int = 2048
    ):
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
        self.hop_length = hop_length
        self.n_fft = n_fft
    
    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Carga audio desde archivo o URL.
        
        Args:
            audio_path: Path local o URL del audio
        
        Returns:
            tuple: (audio_data, sample_rate)
        """
        # Cargar audio con librosa
        y, sr = librosa.load(audio_path, sr=self.sample_rate, mono=True)
        
        # Normalizar volumen
        y = librosa.util.normalize(y)
        
        return y, sr
    
    def extract_mfcc_features(self, y: np.ndarray) -> Dict:
        """
        Extrae MFCCs y sus deltas.
        
        Args:
            y: Audio signal
        
        Returns:
            dict: MFCCs con estadísticas
        """
        # Extraer MFCCs
        mfccs = librosa.feature.mfcc(
            y=y,
            sr=self.sample_rate,
            n_mfcc=self.n_mfcc,
            hop_length=self.hop_length,
            n_fft=self.n_fft
        )
        
        # Deltas
        mfcc_delta = librosa.feature.delta(mfccs)
        mfcc_delta2 = librosa.feature.delta(mfccs, order=2)
        
        # Calcular estadísticas (por coeficiente)
        mfcc_stats = {
            "coefficients": mfccs.tolist(),  # [13 x frames]
            "delta": mfcc_delta.tolist(),
            "delta_delta": mfcc_delta2.tolist(),
            "stats": {
                "mean": np.mean(mfccs, axis=1).tolist(),     # 13 valores
                "std": np.std(mfccs, axis=1).tolist(),       # 13 valores
                "min": np.min(mfccs, axis=1).tolist(),       # 13 valores
                "max": np.max(mfccs, axis=1).tolist()        # 13 valores
            }
        }
        
        return mfcc_stats

    def extract_prosody_features(self, audio_path: str) -> Dict:
        """
        Extrae features prosódicos usando Parselmouth (Praat).
        
        Args:
            audio_path: Path del audio
        
        Returns:
            dict: F0, jitter, shimmer, etc.
        """
        # Cargar con Parselmouth
        sound = parselmouth.Sound(audio_path)
        
        # Extraer pitch (F0)
        pitch = call(sound, "To Pitch", 0.0, 75, 600)  # 75-600 Hz (voz humana)
        
        # Obtener valores de F0
        f0_values = []
        for i in range(pitch.get_number_of_frames()):
            f0 = pitch.get_value_in_frame(i)
            if f0 > 0:  # Ignorar frames sin voz
                f0_values.append(f0)
        
        f0_array = np.array(f0_values) if f0_values else np.array([0])
        
        # Point Process para jitter/shimmer
        point_process = call(sound, "To PointProcess (periodic, cc)", 75, 600)
        
        # Calcular jitter (variabilidad de pitch)
        try:
            jitter = call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        except:
            jitter = 0.0
        
        # Calcular shimmer (variabilidad de amplitud)
        try:
            shimmer = call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        except:
            shimmer = 0.0
        
        # ✅ CORRECCIÓN AQUÍ: Extraer energía
        intensity = call(sound, "To Intensity", 75, 0.0, "yes")
        energy_values = []
        
        # ✅ CAMBIO: usar get_number_of_frames() y values[i] en lugar de get_value_in_frame
        intensity_values = intensity.values[0]  # Obtener array de valores
        for value in intensity_values:
            if value > 0:
                energy_values.append(float(value))
        
        energy_array = np.array(energy_values) if energy_values else np.array([0])
        
        prosody_stats = {
            "f0_curve": f0_values,  # Curva completa
            "f0_stats": {
                "mean": float(np.mean(f0_array)) if len(f0_array) > 0 else 0.0,
                "std": float(np.std(f0_array)) if len(f0_array) > 0 else 0.0,
                "min": float(np.min(f0_array)) if len(f0_array) > 0 else 0.0,
                "max": float(np.max(f0_array)) if len(f0_array) > 0 else 0.0,
                "median": float(np.median(f0_array)) if len(f0_array) > 0 else 0.0,
                "range": float(np.max(f0_array) - np.min(f0_array)) if len(f0_array) > 0 else 0.0
            },
            "jitter": float(jitter),
            "shimmer": float(shimmer),
            "energy_contour": energy_values,
            "energy_stats": {
                "mean": float(np.mean(energy_array)),
                "std": float(np.std(energy_array))
            }
        }

        return prosody_stats
        
    
    def segment_phonemes_simple(
        self,
        y: np.ndarray,
        text_content: str
    ) -> List[Dict]:
        """
        Segmentación fonética simplificada (sin Forced Aligner).
        
        Divide el audio en segmentos basados en energía.
        Para producción, deberías usar Montreal Forced Aligner.
        
        Args:
            y: Audio signal
            text_content: Texto del ejercicio
        
        Returns:
            List[Dict]: Segmentos detectados
        """
        # Calcular energía RMS
        rms = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
        
        # Detectar inicio/fin de segmentos con energía
        threshold = np.mean(rms) * 0.3
        is_sound = rms > threshold
        
        # Encontrar transiciones
        transitions = np.diff(is_sound.astype(int))
        starts = np.where(transitions == 1)[0]
        ends = np.where(transitions == -1)[0]
        
        # Ajustar si no hay mismo número de starts/ends
        if len(starts) > 0 and len(ends) > 0:
            if starts[0] > ends[0]:
                ends = ends[1:]
            if len(starts) > len(ends):
                starts = starts[:len(ends)]
        
        # Convertir índices a tiempo
        segments = []
        for i, (start, end) in enumerate(zip(starts, ends)):
            start_time = librosa.frames_to_time(start, sr=self.sample_rate, hop_length=self.hop_length)
            end_time = librosa.frames_to_time(end, sr=self.sample_rate, hop_length=self.hop_length)
            
            # Extraer formantes del segmento (simplificado)
            segment_audio = y[int(start_time * self.sample_rate):int(end_time * self.sample_rate)]
            
            if len(segment_audio) > 0:
                # Calcular espectro para formantes aproximados
                spectrum = np.abs(np.fft.rfft(segment_audio))
                freqs = np.fft.rfftfreq(len(segment_audio), 1/self.sample_rate)
                
                # Encontrar picos (formantes aproximados)
                from scipy.signal import find_peaks
                peaks, _ = find_peaks(spectrum, height=np.max(spectrum) * 0.1)
                
                formant_freqs = freqs[peaks[:3]] if len(peaks) >= 3 else [0, 0, 0]
                while len(formant_freqs) < 3:
                    formant_freqs = np.append(formant_freqs, 0)
                
                segments.append({
                    "phoneme": f"seg_{i+1}",  # Sin transcripción real
                    "start_time": float(start_time),
                    "end_time": float(end_time),
                    "duration_ms": int((end_time - start_time) * 1000),
                    "formant_f1": float(formant_freqs[0]),
                    "formant_f2": float(formant_freqs[1]),
                    "formant_f3": float(formant_freqs[2]),
                    "position_in_word": "media"  # Placeholder
                })
        
        return segments
    
    def calculate_all_features(
        self,
        audio_path: str,
        text_content: str
    ) -> Dict:
        """
        Calcula todas las features de un audio de referencia.
        
        Args:
            audio_path: Path o URL del audio
            text_content: Texto del ejercicio
        
        Returns:
            dict: Todas las features calculadas
        """
        print(f"  📊 Extrayendo features de: {audio_path}")
        
        # Cargar audio
        y, sr = self.load_audio(audio_path)
        duration = librosa.get_duration(y=y, sr=sr)
        
        print(f"     ⏱️  Duración: {duration:.2f}s")
        
        # Extraer MFCCs
        print(f"     🎵 Extrayendo MFCCs...")
        mfcc_features = self.extract_mfcc_features(y)
        
        # Extraer prosodia
        print(f"     🎤 Extrayendo prosodia (F0, jitter, shimmer)...")
        prosody_features = self.extract_prosody_features(audio_path)
        
        # Segmentación simple
        print(f"     ✂️  Segmentando audio...")
        phoneme_segments = self.segment_phonemes_simple(y, text_content)
        
        # Calcular parámetros de normalización
        normalization_params = {
            "mfcc_mean": mfcc_features["stats"]["mean"],
            "mfcc_std": mfcc_features["stats"]["std"],
            "f0_range": [
                prosody_features["f0_stats"]["min"],
                prosody_features["f0_stats"]["max"]
            ],
            "energy_range": [
                prosody_features["energy_stats"]["mean"] - prosody_features["energy_stats"]["std"],
                prosody_features["energy_stats"]["mean"] + prosody_features["energy_stats"]["std"]
            ]
        }
        
        print(f"     ✅ Features extraídas exitosamente!")
        
        return {
            "mfcc": mfcc_features,
            "prosody": prosody_features,
            "phoneme_segments": phoneme_segments,
            "duration_seconds": float(duration),
            "phoneme_count": len(phoneme_segments),
            "normalization_params": normalization_params,
            "thresholds": {
                "dtw_good": 0.15,
                "dtw_acceptable": 0.30,
                "dtw_poor": 0.50,
                "phoneme_duration_tolerance": 0.20,
                "f0_tolerance": 0.15
            }
        }