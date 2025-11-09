"""
Value Object QualityCheck - Resultado de validación de calidad de audio.
"""

from dataclasses import dataclass, field
from typing import List
from enum import Enum


class QualityIssue(str, Enum):
    """Tipos de problemas de calidad"""
    AUDIO_TOO_SHORT = "audio_too_short"
    AUDIO_TOO_LONG = "audio_too_long"
    LOW_SNR = "low_snr"  # Signal-to-Noise Ratio bajo
    EXCESSIVE_BACKGROUND_NOISE = "excessive_background_noise"
    CLIPPING_DETECTED = "clipping_detected"  # Audio saturado
    SILENCE_DETECTED = "silence_detected"
    LOW_VOLUME = "low_volume"
    UNEXPECTED_FORMAT = "unexpected_format"


@dataclass(frozen=True)
class QualityCheck:
    """
    Value Object que representa el resultado de validación de calidad.
    
    Attributes:
        is_valid: Si el audio pasa la validación
        quality_score: Puntuación de calidad 0-10
        snr_db: Signal-to-Noise Ratio en dB
        issues: Lista de problemas encontrados
        warnings: Advertencias no críticas
        rejection_reason: Razón de rechazo si is_valid=False
    """
    
    is_valid: bool
    quality_score: float  # 0-10
    snr_db: float
    issues: List[QualityIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rejection_reason: str = ""
    
    # Metadata adicional
    has_clipping: bool = False
    has_background_noise: bool = False
    duration_seconds: float = 0.0
    volume_level: float = 0.0  # RMS promedio
    
    def __post_init__(self):
        """Validaciones"""
        if not 0 <= self.quality_score <= 10:
            raise ValueError("quality_score debe estar entre 0 y 10")
    
    def is_excellent(self) -> bool:
        """Calidad excelente (>= 9.0)"""
        return self.quality_score >= 9.0
    
    def is_good(self) -> bool:
        """Calidad buena (>= 7.0)"""
        return self.quality_score >= 7.0
    
    def is_acceptable(self) -> bool:
        """Calidad aceptable (>= 5.0)"""
        return self.quality_score >= 5.0
    
    def has_critical_issues(self) -> bool:
        """Tiene problemas críticos"""
        critical_issues = {
            QualityIssue.AUDIO_TOO_SHORT,
            QualityIssue.AUDIO_TOO_LONG,
            QualityIssue.LOW_SNR,
            QualityIssue.CLIPPING_DETECTED
        }
        return any(issue in critical_issues for issue in self.issues)
    
    def get_recommendation(self) -> str:
        """Obtiene recomendación para el usuario"""
        if self.is_valid:
            if self.is_excellent():
                return "Audio de excelente calidad. ¡Perfecto!"
            elif self.is_good():
                return "Audio de buena calidad. Puedes continuar."
            else:
                return "Audio aceptable. Intenta grabar en un lugar más silencioso para mejores resultados."
        
        # Audio rechazado - dar recomendación específica
        if QualityIssue.AUDIO_TOO_SHORT in self.issues:
            return "El audio es muy corto. Intenta pronunciar la palabra completa."
        elif QualityIssue.AUDIO_TOO_LONG in self.issues:
            return "El audio es muy largo. Intenta ser más conciso."
        elif QualityIssue.LOW_SNR in self.issues or QualityIssue.EXCESSIVE_BACKGROUND_NOISE in self.issues:
            return "Hay mucho ruido de fondo. Por favor, graba en un lugar más silencioso."
        elif QualityIssue.CLIPPING_DETECTED in self.issues:
            return "El audio está saturado. Aleja un poco el micrófono y vuelve a grabar."
        elif QualityIssue.LOW_VOLUME in self.issues:
            return "El volumen es muy bajo. Acerca el micrófono y habla más fuerte."
        elif QualityIssue.SILENCE_DETECTED in self.issues:
            return "No se detectó voz en el audio. Asegúrate de hablar durante la grabación."
        
        return self.rejection_reason or "La calidad del audio no es aceptable. Por favor, intenta grabar nuevamente."
    
    def to_dict(self) -> dict:
        from src.audio_processing.infrastructure.helpers.nunpy_json_encoder import safe_float, safe_bool
        return {
            "is_valid": safe_bool(self.is_valid),
            "quality_score": safe_float(self.quality_score),
            "snr_db": safe_float(self.snr_db),
            "has_background_noise": safe_bool(self.has_background_noise),
            "has_clipping": safe_bool(self.has_clipping),
            "duration_seconds": safe_float(self.duration_seconds),
            "rejection_reason": self.rejection_reason,
            "recommendation": self.get_recommendation()
        }
    
    def __repr__(self) -> str:
        status = "VALID" if self.is_valid else "REJECTED"
        return f"QualityCheck({status}, score={self.quality_score:.1f}, snr={self.snr_db:.1f}dB)"