"""
AudioValidator - Valida la calidad del audio.
"""

import numpy as np
import librosa
from typing import List
from src.audio_processing.domain.models.audio import Audio
from src.audio_processing.domain.models.quality_check import QualityCheck, QualityIssue


class AudioValidator:
    """
    Validador de calidad de audio.
    
    Verifica:
    - Duración (min/max)
    - SNR (Signal-to-Noise Ratio)
    - Clipping (saturación)
    - Ruido de fondo
    - Nivel de volumen
    """
    
    def __init__(
        self,
        min_duration_seconds: float = 0.3,
        max_duration_seconds: float = 10.0,
        min_snr_db: float = 10.0,
        min_quality_score: float = 6.0
    ):
        """
        Args:
            min_duration_seconds: Duración mínima aceptable
            max_duration_seconds: Duración máxima aceptable
            min_snr_db: SNR mínimo aceptable (dB)
            min_quality_score: Score mínimo de calidad (0-10)
        """
        self.min_duration = min_duration_seconds
        self.max_duration = max_duration_seconds
        self.min_snr_db = min_snr_db
        self.min_quality_score = min_quality_score
    
    def validate(self, audio: Audio) -> QualityCheck:
        """
        Valida la calidad del audio.
        
        Args:
            audio: Audio a validar
        
        Returns:
            QualityCheck: Resultado de la validación
        """
        issues: List[QualityIssue] = []
        warnings: List[str] = []
        
        # 1. Validar duración
        duration = audio.metadata.duration_seconds
        
        if duration < self.min_duration:
            issues.append(QualityIssue.AUDIO_TOO_SHORT)
        elif duration > self.max_duration:
            issues.append(QualityIssue.AUDIO_TOO_LONG)
        
        # 2. Calcular SNR (Signal-to-Noise Ratio)
        snr_db = self._calculate_snr(audio.data)
        
        if snr_db < self.min_snr_db:
            issues.append(QualityIssue.LOW_SNR)
        
        # 3. Detectar clipping (saturación)
        has_clipping = self._detect_clipping(audio.data)
        if has_clipping:
            issues.append(QualityIssue.CLIPPING_DETECTED)
        
        # 4. Detectar silencio
        is_silent = self._detect_silence(audio.data)
        if is_silent:
            issues.append(QualityIssue.SILENCE_DETECTED)
        
        # 5. Verificar nivel de volumen
        volume_level = self._calculate_volume(audio.data)
        
        if volume_level < 0.01:  # Muy bajo
            issues.append(QualityIssue.LOW_VOLUME)
        
        # 6. Detectar ruido de fondo excesivo
        has_background_noise = snr_db < 15.0  # Threshold para ruido
        if has_background_noise and snr_db >= self.min_snr_db:
            warnings.append("Se detectó ruido de fondo. Intenta grabar en un lugar más silencioso.")
        
        # 7. Calcular score de calidad (0-10)
        quality_score = self._calculate_quality_score(
            duration=duration,
            snr_db=snr_db,
            has_clipping=has_clipping,
            volume_level=volume_level,
            is_silent=is_silent
        )
        
        # 8. Determinar si es válido
        is_valid = (
            len(issues) == 0 and
            quality_score >= self.min_quality_score
        )
        
        # 9. Generar razón de rechazo
        rejection_reason = ""
        if not is_valid:
            if QualityIssue.AUDIO_TOO_SHORT in issues:
                rejection_reason = "El audio es muy corto"
            elif QualityIssue.AUDIO_TOO_LONG in issues:
                rejection_reason = "El audio es muy largo"
            elif QualityIssue.LOW_SNR in issues:
                rejection_reason = "Demasiado ruido de fondo"
            elif QualityIssue.CLIPPING_DETECTED in issues:
                rejection_reason = "Audio saturado"
            elif QualityIssue.SILENCE_DETECTED in issues:
                rejection_reason = "No se detectó voz"
            elif QualityIssue.LOW_VOLUME in issues:
                rejection_reason = "Volumen muy bajo"
            else:
                rejection_reason = "La calidad del audio no es aceptable"
        
        return QualityCheck(
            is_valid=is_valid,
            quality_score=quality_score,
            snr_db=snr_db,
            issues=issues,
            warnings=warnings,
            rejection_reason=rejection_reason,
            has_clipping=has_clipping,
            has_background_noise=has_background_noise,
            duration_seconds=duration,
            volume_level=volume_level
        )
    
    def _calculate_snr(self, y: np.ndarray) -> float:
        """
        Calcula el Signal-to-Noise Ratio.
        
        Args:
            y: Audio signal
        
        Returns:
            float: SNR en dB
        """
        # Calcular energía RMS
        rms = np.sqrt(np.mean(y**2))
        
        # Estimar ruido (primeros y últimos 10% del audio)
        noise_start = y[:int(len(y) * 0.1)]
        noise_end = y[int(len(y) * 0.9):]
        noise = np.concatenate([noise_start, noise_end])
        noise_rms = np.sqrt(np.mean(noise**2))
        
        # Evitar división por cero
        if noise_rms < 1e-10:
            noise_rms = 1e-10
        
        # Calcular SNR en dB
        snr = 20 * np.log10(rms / noise_rms)
        
        return float(snr)
    
    def _detect_clipping(self, y: np.ndarray, threshold: float = 0.99) -> bool:
        """
        Detecta si el audio está saturado (clipping).
        
        Args:
            y: Audio signal
            threshold: Threshold para considerar clipping (0-1)
        
        Returns:
            bool: True si hay clipping
        """
        # Contar cuántas muestras están cerca del máximo
        clipped_samples = np.sum(np.abs(y) >= threshold)
        clipped_percentage = clipped_samples / len(y)
        
        # Si más del 1% de las muestras están saturadas
        return clipped_percentage > 0.01
    
    def _detect_silence(self, y: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Detecta si el audio es mayormente silencio.
        
        Args:
            y: Audio signal
            threshold: Threshold de energía
        
        Returns:
            bool: True si es silencio
        """
        # Calcular energía RMS
        rms = np.sqrt(np.mean(y**2))
        
        return rms < threshold
    
    def _calculate_volume(self, y: np.ndarray) -> float:
        """
        Calcula el nivel de volumen (RMS).
        
        Args:
            y: Audio signal
        
        Returns:
            float: Nivel de volumen (0-1)
        """
        return float(np.sqrt(np.mean(y**2)))
    
    def _calculate_quality_score(
        self,
        duration: float,
        snr_db: float,
        has_clipping: bool,
        volume_level: float,
        is_silent: bool
    ) -> float:
        """
        Calcula un score de calidad general (0-10).
        
        Args:
            duration: Duración del audio
            snr_db: SNR en dB
            has_clipping: Si tiene clipping
            volume_level: Nivel de volumen
            is_silent: Si es silencio
        
        Returns:
            float: Score de calidad (0-10)
        """
        score = 10.0
        
        # Penalizar por duración
        if duration < self.min_duration:
            score -= 5.0
        elif duration > self.max_duration:
            score -= 3.0
        
        # Penalizar por SNR bajo
        if snr_db < 10:
            score -= 4.0
        elif snr_db < 15:
            score -= 2.0
        elif snr_db < 20:
            score -= 1.0
        
        # Penalizar por clipping
        if has_clipping:
            score -= 3.0
        
        # Penalizar por volumen bajo
        if volume_level < 0.01:
            score -= 4.0
        elif volume_level < 0.05:
            score -= 2.0
        
        # Penalizar por silencio
        if is_silent:
            score -= 5.0
        
        # Bonus por buena calidad
        if snr_db > 25:
            score += 0.5
        if 0.1 < volume_level < 0.8:  # Volumen óptimo
            score += 0.5
        
        # Asegurar rango [0, 10]
        return max(0.0, min(10.0, score))

