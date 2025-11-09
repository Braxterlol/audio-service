"""
FeatureExtractor - Orquestador principal de extracción de características.
"""

import numpy as np
from typing import Dict, List
from src.audio_processing.domain.models.audio import Audio
from src.audio_processing.domain.models.audio_features import (
    AudioFeatures,
    MFCCFeatures,
    ProsodyFeatures,
    RhythmFeatures,
    PhonemeSegment
)
from src.audio_processing.infrastructure.helpers.mfcc_extractor import MFCCExtractor
from src.audio_processing.infrastructure.helpers.prosody_analyzer import ProsodyAnalyzer
from src.audio_processing.infrastructure.helpers.rhythm_analyzer import RhythmAnalyzer


class FeatureExtractor:
    """
    Orquestador principal de extracción de características.
    
    Coordina todos los extractores especializados y construye
    el objeto AudioFeatures del dominio.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        n_mfcc: int = 13,
        f0_min: float = 75.0,
        f0_max: float = 500.0
    ):
        """
        Args:
            sample_rate: Frecuencia de muestreo objetivo
            n_mfcc: Número de coeficientes MFCC
            f0_min: F0 mínimo para análisis de pitch
            f0_max: F0 máximo para análisis de pitch
        """
        self.sample_rate = sample_rate
        
        # Inicializar extractores especializados
        self.mfcc_extractor = MFCCExtractor(n_mfcc=n_mfcc)
        self.prosody_analyzer = ProsodyAnalyzer(f0_min=f0_min, f0_max=f0_max)
        self.rhythm_analyzer = RhythmAnalyzer()
    
    def extract_all_features(
        self,
        audio: Audio,
        attempt_id: str,
        exercise_id: str,
        user_id: str
    ) -> AudioFeatures:
        """
        Extrae todas las características del audio y construye AudioFeatures.
        
        Args:
            audio: Audio del cual extraer características
            attempt_id: UUID del intento
            exercise_id: ID del ejercicio
            user_id: UUID del usuario
        
        Returns:
            AudioFeatures: Objeto con todas las características estructuradas
        """
        # 1. Extraer MFCCs raw
        mfccs_raw = self.mfcc_extractor.extract_raw_mfccs(audio)
        mfcc_delta = np.gradient(mfccs_raw, axis=1)  # Deltas manualmente
        mfcc_delta2 = np.gradient(mfcc_delta, axis=1)  # Delta-deltas
        
        # Crear MFCCFeatures
        mfcc_features = MFCCFeatures(
            coefficients=mfccs_raw.tolist(),
            delta=mfcc_delta.tolist(),
            delta_delta=mfcc_delta2.tolist(),
            stats={
                "mean": np.mean(mfccs_raw, axis=1).tolist(),
                "std": np.std(mfccs_raw, axis=1).tolist(),
                "min": np.min(mfccs_raw, axis=1).tolist(),
                "max": np.max(mfccs_raw, axis=1).tolist()
            }
        )
        
        # 2. Extraer prosodia
        prosody_dict = self.prosody_analyzer.extract(audio)
        
        # Extraer F0 curve completa
        import librosa
        f0_curve = librosa.yin(
            audio.data,
            fmin=self.prosody_analyzer.f0_min,
            fmax=self.prosody_analyzer.f0_max,
            sr=audio.metadata.sample_rate
        )
        f0_curve_list = [float(f) for f in f0_curve if f > 0]
        
        # Crear ProsodyFeatures
        prosody_features = ProsodyFeatures(
            f0_curve=f0_curve_list,
            f0_stats={
                "mean": prosody_dict['f0_mean'],
                "std": prosody_dict['f0_std'],
                "min": prosody_dict['f0_min'],
                "max": prosody_dict['f0_max'],
                "median": prosody_dict['f0_median'],
                "range": prosody_dict['f0_range']
            },
            jitter=prosody_dict['jitter_local'],
            shimmer=prosody_dict['shimmer_local'],
            energy_contour=[],  # TODO: extraer energy contour si es necesario
            energy_stats={
                "mean": prosody_dict['intensity_mean'],
                "std": prosody_dict['intensity_std']
            }
        )
        
        # 3. Extraer ritmo
        rhythm_dict = self.rhythm_analyzer.extract(audio)
        
        # Detectar pausas para durations
        pauses = self.rhythm_analyzer._detect_pauses(
            audio.data,
            audio.metadata.sample_rate
        )
        pause_durations_ms = [int((p[1] - p[0]) * 1000) for p in pauses]
        
        # Crear RhythmFeatures
        rhythm_features = RhythmFeatures(
            speech_rate=rhythm_dict['speech_rate'],
            articulation_rate=rhythm_dict['articulation_rate'],
            pause_count=int(rhythm_dict['num_pauses']),
            pause_durations_ms=pause_durations_ms,
            total_pause_time_ms=int(rhythm_dict['total_pause_time'] * 1000),
            speaking_time_ms=int(rhythm_dict['total_speech_time'] * 1000),
            total_duration_ms=int(audio.metadata.duration_seconds * 1000)
        )
        
        # 4. Segmentos fonéticos (simplificado por ahora)
        # TODO: Implementar segmentación real con Forced Aligner
        phoneme_segments: List[PhonemeSegment] = []
        
        # 5. Construir AudioFeatures final
        audio_features = AudioFeatures(
            attempt_id=attempt_id,
            exercise_id=exercise_id,
            user_id=user_id,
            mfcc=mfcc_features,
            prosody=prosody_features,
            rhythm=rhythm_features,
            phoneme_segments=phoneme_segments,
            duration_seconds=audio.metadata.duration_seconds,
            phoneme_count=0,  # Se actualizará cuando tengamos segmentación
            processing_version="v1.0"
        )
        
        return audio_features
    
    def extract_features_dict(self, audio: Audio) -> Dict[str, float]:
        """
        Extrae características como diccionario flat (útil para análisis rápido).
        
        Args:
            audio: Audio del cual extraer características
        
        Returns:
            Dict con todas las características
        """
        mfcc_features = self.mfcc_extractor.extract(audio)
        prosody_features = self.prosody_analyzer.extract(audio)
        rhythm_features = self.rhythm_analyzer.extract(audio)
        
        return {
            **mfcc_features,
            **prosody_features,
            **rhythm_features
        }
    
    def compare_audios(
        self,
        user_audio: Audio,
        reference_audio: Audio
    ) -> Dict[str, float]:
        """
        Compara dos audios y genera scores de similitud.
        
        Args:
            user_audio: Audio del usuario
            reference_audio: Audio de referencia
        
        Returns:
            Dict con scores de similitud por categoría
        """
        # Comparar MFCCs (pronunciación/timbre)
        mfcc_score = self.mfcc_extractor.compare_mfccs(
            user_audio,
            reference_audio,
            method="dtw"
        )
        
        # Comparar prosodia (entonación)
        prosody_comparison = self.prosody_analyzer.compare_prosody(
            user_audio,
            reference_audio
        )
        
        # Comparar ritmo (pausas, velocidad)
        rhythm_comparison = self.rhythm_analyzer.compare_rhythm(
            user_audio,
            reference_audio
        )
        
        # Calcular score global ponderado
        overall_score = (
            mfcc_score * 0.5 +                                          # 50% pronunciación
            prosody_comparison['prosody_overall_similarity'] * 0.3 +    # 30% prosodia
            rhythm_comparison['rhythm_overall_similarity'] * 0.2        # 20% ritmo
        )
        
        return {
            # Scores principales
            'phoneme_score': float(mfcc_score),  # Renamed para consistencia
            'intonation_score': float(prosody_comparison['prosody_overall_similarity']),
            'rhythm_score': float(rhythm_comparison['rhythm_overall_similarity']),
            'overall_score': float(overall_score),
            
            # Desglose de prosodia
            'f0_similarity': float(prosody_comparison['f0_similarity']),
            'intensity_similarity': float(prosody_comparison['intensity_similarity']),
            
            # Desglose de ritmo
            'speech_rate_similarity': float(rhythm_comparison['speech_rate_similarity']),
            'pause_similarity': float(rhythm_comparison['pause_similarity']),
        }
    
    def get_feature_summary(self, audio: Audio) -> Dict[str, any]:
        """
        Obtiene un resumen legible de las características.
        
        Args:
            audio: Audio a analizar
        
        Returns:
            Dict con resumen de características
        """
        features = self.extract_features_dict(audio)
        
        return {
            # Información básica
            'duration': audio.metadata.duration_seconds,
            'sample_rate': audio.metadata.sample_rate,
            
            # Pitch (F0)
            'pitch': {
                'mean_hz': features.get('f0_mean', 0),
                'range_hz': features.get('f0_range', 0),
                'variability': features.get('f0_std', 0)
            },
            
            # Intensidad
            'intensity': {
                'mean_db': features.get('intensity_mean', 0),
                'range_db': features.get('intensity_range', 0)
            },
            
            # Calidad de voz
            'voice_quality': {
                'jitter': features.get('jitter_local', 0),
                'shimmer': features.get('shimmer_local', 0),
                'hnr': features.get('hnr', 0)
            },
            
            # Ritmo
            'rhythm': {
                'speech_rate': features.get('speech_rate', 0),
                'num_pauses': features.get('num_pauses', 0),
                'mean_pause_duration': features.get('mean_pause_duration', 0),
                'tempo': features.get('tempo', 0)
            },
            
            # MFCCs (resumen)
            'spectral': {
                'mfcc_mean': features.get('mfcc_overall_mean', 0),
                'mfcc_std': features.get('mfcc_overall_std', 0)
            }
        }
    
    def validate_features(self, audio_features: AudioFeatures) -> bool:
        """
        Valida que las características extraídas sean válidas.
        
        Args:
            audio_features: AudioFeatures a validar
        
        Returns:
            bool: True si las características son válidas
        """
        # Verificar que los stats de MFCC no estén vacíos
        if len(audio_features.mfcc.stats['mean']) != 13:
            return False
        
        # Verificar que F0 tenga valores razonables
        if not (50 < audio_features.prosody.f0_stats['mean'] < 600):
            return False
        
        # Verificar que la duración sea consistente
        if abs(audio_features.duration_seconds - 
               (audio_features.rhythm.total_duration_ms / 1000)) > 0.1:
            return False
        
        return True