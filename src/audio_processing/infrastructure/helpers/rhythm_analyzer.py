"""
RhythmAnalyzer - Analiza ritmo del habla (pausas, speech rate).
"""

import numpy as np
import librosa
from typing import Dict, List, Tuple
from src.audio_processing.domain.models.audio import Audio


class RhythmAnalyzer:
    """
    Analizador de ritmo del habla.
    
    Extrae:
    - Speech rate (velocidad del habla)
    - Pausas (número, duración, ubicación)
    - Proporción speech/pause
    - Variabilidad del ritmo
    """
    
    def __init__(
        self,
        frame_length: int = 2048,
        hop_length: int = 512,
        silence_threshold: float = -40.0,  # dB
        min_pause_duration: float = 0.15   # segundos
    ):
        """
        Args:
            frame_length: Tamaño de ventana para análisis
            hop_length: Hop entre ventanas
            silence_threshold: Threshold en dB para detectar silencio
            min_pause_duration: Duración mínima para considerar una pausa
        """
        self.frame_length = frame_length
        self.hop_length = hop_length
        self.silence_threshold = silence_threshold
        self.min_pause_duration = min_pause_duration
    
    def extract(self, audio: Audio) -> Dict[str, float]:
        """
        Extrae características de ritmo.
        
        Args:
            audio: Audio del cual extraer características
        
        Returns:
            Dict con características de ritmo
        """
        y = audio.data
        sr = audio.metadata.sample_rate
        duration = audio.metadata.duration_seconds
        
        # Detectar pausas
        pauses = self._detect_pauses(y, sr)
        
        # Calcular características de pausas
        num_pauses = len(pauses)
        
        if num_pauses > 0:
            pause_durations = [p[1] - p[0] for p in pauses]
            total_pause_time = sum(pause_durations)
            mean_pause_duration = np.mean(pause_durations)
            std_pause_duration = np.std(pause_durations)
            max_pause_duration = max(pause_durations)
        else:
            total_pause_time = 0.0
            mean_pause_duration = 0.0
            std_pause_duration = 0.0
            max_pause_duration = 0.0
        
        # Calcular speech time
        total_speech_time = duration - total_pause_time
        
        # Calcular speech rate (proporción de habla)
        if duration > 0:
            speech_rate = total_speech_time / duration
            pause_rate = total_pause_time / duration
        else:
            speech_rate = 0.0
            pause_rate = 0.0
        
        # Detectar segmentos de habla (entre pausas)
        speech_segments = self._get_speech_segments(pauses, duration)
        num_speech_segments = len(speech_segments)
        
        if num_speech_segments > 0:
            speech_durations = [s[1] - s[0] for s in speech_segments]
            mean_speech_duration = np.mean(speech_durations)
            std_speech_duration = np.std(speech_durations)
        else:
            mean_speech_duration = 0.0
            std_speech_duration = 0.0
        
        # Calcular variabilidad del ritmo (usando onset strength)
        rhythm_variability = self._calculate_rhythm_variability(y, sr)
        
        # Calcular tempo (usando onset detection)
        tempo = self._estimate_tempo(y, sr)
        
        # Calcular articulación rate (velocidad sin contar pausas)
        if total_speech_time > 0:
            articulation_rate = num_speech_segments / total_speech_time
        else:
            articulation_rate = 0.0
        
        return {
            # Pausas
            'num_pauses': float(num_pauses),
            'total_pause_time': float(total_pause_time),
            'mean_pause_duration': float(mean_pause_duration),
            'std_pause_duration': float(std_pause_duration),
            'max_pause_duration': float(max_pause_duration),
            'pause_rate': float(pause_rate),
            
            # Habla
            'num_speech_segments': float(num_speech_segments),
            'total_speech_time': float(total_speech_time),
            'mean_speech_duration': float(mean_speech_duration),
            'std_speech_duration': float(std_speech_duration),
            'speech_rate': float(speech_rate),
            'articulation_rate': float(articulation_rate),
            
            # Ritmo
            'rhythm_variability': float(rhythm_variability),
            'tempo': float(tempo)
        }
    
    def _detect_pauses(self, y: np.ndarray, sr: int) -> List[Tuple[float, float]]:
        """
        Detecta pausas en el audio.
        
        Args:
            y: Audio signal
            sr: Sample rate
        
        Returns:
            Lista de tuplas (inicio, fin) en segundos
        """
        # Calcular RMS energy
        rms = librosa.feature.rms(
            y=y,
            frame_length=self.frame_length,
            hop_length=self.hop_length
        )[0]
        
        # Convertir a dB
        rms_db = librosa.amplitude_to_db(rms, ref=np.max)
        
        # Detectar frames silenciosos
        is_silent = rms_db < self.silence_threshold
        
        # Convertir frames a tiempo
        times = librosa.frames_to_time(
            np.arange(len(rms_db)),
            sr=sr,
            hop_length=self.hop_length
        )
        
        # Encontrar intervalos de silencio
        pauses = []
        in_pause = False
        pause_start = 0.0
        
        for i, silent in enumerate(is_silent):
            if silent and not in_pause:
                # Inicio de pausa
                in_pause = True
                pause_start = times[i]
            elif not silent and in_pause:
                # Fin de pausa
                pause_end = times[i]
                pause_duration = pause_end - pause_start
                
                # Solo agregar si supera duración mínima
                if pause_duration >= self.min_pause_duration:
                    pauses.append((pause_start, pause_end))
                
                in_pause = False
        
        # Cerrar última pausa si quedó abierta
        if in_pause:
            pause_end = times[-1]
            pause_duration = pause_end - pause_start
            if pause_duration >= self.min_pause_duration:
                pauses.append((pause_start, pause_end))
        
        return pauses
    
    def _get_speech_segments(
        self,
        pauses: List[Tuple[float, float]],
        total_duration: float
    ) -> List[Tuple[float, float]]:
        """
        Obtiene segmentos de habla (entre pausas).
        
        Args:
            pauses: Lista de pausas (inicio, fin)
            total_duration: Duración total del audio
        
        Returns:
            Lista de segmentos de habla (inicio, fin)
        """
        if len(pauses) == 0:
            return [(0.0, total_duration)]
        
        segments = []
        
        # Primer segmento (antes de la primera pausa)
        if pauses[0][0] > 0.0:
            segments.append((0.0, pauses[0][0]))
        
        # Segmentos entre pausas
        for i in range(len(pauses) - 1):
            segment_start = pauses[i][1]
            segment_end = pauses[i + 1][0]
            if segment_end > segment_start:
                segments.append((segment_start, segment_end))
        
        # Último segmento (después de la última pausa)
        if pauses[-1][1] < total_duration:
            segments.append((pauses[-1][1], total_duration))
        
        return segments
    
    def _calculate_rhythm_variability(self, y: np.ndarray, sr: int) -> float:
        """
        Calcula la variabilidad del ritmo.
        
        Args:
            y: Audio signal
            sr: Sample rate
        
        Returns:
            float: Variabilidad del ritmo (0-1)
        """
        # Calcular onset strength envelope
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        
        # Calcular variabilidad (coeficiente de variación)
        if np.mean(onset_env) > 0:
            variability = np.std(onset_env) / np.mean(onset_env)
        else:
            variability = 0.0
        
        return float(variability)
    
    def _estimate_tempo(self, y: np.ndarray, sr: int) -> float:
        """
        Estima el tempo (velocidad) del habla.
        
        Args:
            y: Audio signal
            sr: Sample rate
        
        Returns:
            float: Tempo estimado (BPM)
        """
        # Calcular onset strength
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        
        # Estimar tempo
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        
        return float(tempo)
    
    def compare_rhythm(
        self,
        audio1: Audio,
        audio2: Audio
    ) -> Dict[str, float]:
        """
        Compara el ritmo entre dos audios.
        
        Args:
            audio1: Audio del usuario
            audio2: Audio de referencia
        
        Returns:
            Dict con scores de similitud
        """
        features1 = self.extract(audio1)
        features2 = self.extract(audio2)
        
        # Comparar speech rate
        speech_rate_diff = abs(features1['speech_rate'] - features2['speech_rate'])
        speech_rate_similarity = max(0, 100 - speech_rate_diff * 100)
        
        # Comparar número de pausas (normalizado por duración)
        pauses1_per_sec = features1['num_pauses'] / audio1.metadata.duration_seconds
        pauses2_per_sec = features2['num_pauses'] / audio2.metadata.duration_seconds
        pause_diff = abs(pauses1_per_sec - pauses2_per_sec)
        pause_similarity = max(0, 100 - pause_diff * 50)
        
        # Comparar tempo
        tempo_diff = abs(features1['tempo'] - features2['tempo'])
        tempo_similarity = max(0, 100 - (tempo_diff / features2['tempo']) * 100)
        
        # Comparar variabilidad del ritmo
        rhythm_var_diff = abs(features1['rhythm_variability'] - features2['rhythm_variability'])
        rhythm_var_similarity = max(0, 100 - rhythm_var_diff * 100)
        
        return {
            'speech_rate_similarity': float(speech_rate_similarity),
            'pause_similarity': float(pause_similarity),
            'tempo_similarity': float(tempo_similarity),
            'rhythm_variability_similarity': float(rhythm_var_similarity),
            'rhythm_overall_similarity': float(
                (speech_rate_similarity * 0.4 +
                 pause_similarity * 0.3 +
                 tempo_similarity * 0.2 +
                 rhythm_var_similarity * 0.1)
            )
        }

