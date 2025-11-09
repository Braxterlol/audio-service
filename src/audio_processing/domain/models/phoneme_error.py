"""
Entidad PhonemeError - Representa un error fonético detectado.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ErrorType(str, Enum):
    """Tipos de errores fonéticos"""
    OMISION = "omision"  # Omitió el fonema
    SUSTITUCION = "sustitucion"  # Sustituyó por otro fonema
    DISTORSION = "distorsion"  # Lo pronunció mal
    ADICION = "adicion"  # Agregó un fonema extra
    DURACION_INCORRECTA = "duracion_incorrecta"  # Duración incorrecta


class PhonemePosition(str, Enum):
    """Posición del fonema en la palabra"""
    INICIAL = "inicial"
    MEDIA = "media"
    FINAL = "final"
    AISLADO = "aislado"


@dataclass
class PhonemeError:
    """
    Entidad que representa un error fonético detectado.
    
    Attributes:
        id: Identificador único
        attempt_id: ID del intento al que pertenece
        phoneme: Fonema objetivo
        target_phoneme: Fonema que debería ser (opcional)
        error_type: Tipo de error
        position_in_word: Posición del fonema
        severity: Severidad del error (0-10)
        formant_f1, f2, f3: Formantes del fonema mal pronunciado
        duration_ms: Duración del fonema
        start_time_seconds: Tiempo de inicio en el audio
        end_time_seconds: Tiempo de fin en el audio
        detected_at: Fecha de detección
    """
    
    id: str
    attempt_id: str
    
    phoneme: str
    target_phoneme: str = ""
    
    error_type: ErrorType = ErrorType.DISTORSION
    position_in_word: PhonemePosition = PhonemePosition.MEDIA
    severity: float = 5.0  # 0-10, donde 10 es muy grave
    
    # Features acústicos del error
    formant_f1: float = 0.0
    formant_f2: float = 0.0
    formant_f3: float = 0.0
    duration_ms: int = 0
    
    # Ubicación temporal
    start_time_seconds: float = 0.0
    end_time_seconds: float = 0.0
    
    detected_at: datetime = None
    
    def __post_init__(self):
        """Validaciones y defaults"""
        if self.detected_at is None:
            object.__setattr__(self, 'detected_at', datetime.utcnow())
        
        if not 0 <= self.severity <= 10:
            raise ValueError("severity debe estar entre 0 y 10")
        
        if not self.phoneme:
            raise ValueError("phoneme no puede estar vacío")
    
    def is_critical(self) -> bool:
        """Error crítico (severidad >= 8)"""
        return self.severity >= 8.0
    
    def is_moderate(self) -> bool:
        """Error moderado (5 <= severidad < 8)"""
        return 5.0 <= self.severity < 8.0
    
    def is_minor(self) -> bool:
        """Error menor (severidad < 5)"""
        return self.severity < 5.0
    
    def get_description(self) -> str:
        """Obtiene descripción legible del error"""
        descriptions = {
            ErrorType.OMISION: f"Omitió el fonema {self.phoneme}",
            ErrorType.SUSTITUCION: f"Sustituyó {self.target_phoneme or '?'} por {self.phoneme}",
            ErrorType.DISTORSION: f"Distorsionó el fonema {self.phoneme}",
            ErrorType.ADICION: f"Agregó el fonema {self.phoneme}",
            ErrorType.DURACION_INCORRECTA: f"Duración incorrecta del fonema {self.phoneme}"
        }
        return descriptions.get(self.error_type, f"Error en {self.phoneme}")
    
    def get_recommendation(self) -> str:
        """Obtiene recomendación para corregir el error"""
        if self.error_type == ErrorType.OMISION:
            return f"Asegúrate de pronunciar el sonido {self.phoneme}"
        elif self.error_type == ErrorType.SUSTITUCION:
            return f"Enfócate en diferenciar {self.target_phoneme} de {self.phoneme}"
        elif self.error_type == ErrorType.DISTORSION:
            return f"Practica la pronunciación correcta de {self.phoneme}"
        elif self.error_type == ErrorType.DURACION_INCORRECTA:
            return f"Intenta sostener el sonido {self.phoneme} el tiempo adecuado"
        return "Practica este fonema con ejercicios específicos"
    
    def to_dict(self) -> dict:
        """Convierte a diccionario"""
        return {
            "id": self.id,
            "attempt_id": self.attempt_id,
            "phoneme": self.phoneme,
            "target_phoneme": self.target_phoneme,
            "error_type": self.error_type.value,
            "position_in_word": self.position_in_word.value,
            "severity": round(self.severity, 2),
            "formant_f1": round(self.formant_f1, 2),
            "formant_f2": round(self.formant_f2, 2),
            "formant_f3": round(self.formant_f3, 2),
            "duration_ms": self.duration_ms,
            "start_time_seconds": round(self.start_time_seconds, 3),
            "end_time_seconds": round(self.end_time_seconds, 3),
            "detected_at": self.detected_at.isoformat(),
            "description": self.get_description(),
            "recommendation": self.get_recommendation()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PhonemeError':
        """Crea instancia desde diccionario"""
        return cls(
            id=data['id'],
            attempt_id=data['attempt_id'],
            phoneme=data['phoneme'],
            target_phoneme=data.get('target_phoneme', ''),
            error_type=ErrorType(data['error_type']),
            position_in_word=PhonemePosition(data['position_in_word']),
            severity=data['severity'],
            formant_f1=data.get('formant_f1', 0.0),
            formant_f2=data.get('formant_f2', 0.0),
            formant_f3=data.get('formant_f3', 0.0),
            duration_ms=data.get('duration_ms', 0),
            start_time_seconds=data.get('start_time_seconds', 0.0),
            end_time_seconds=data.get('end_time_seconds', 0.0),
            detected_at=datetime.fromisoformat(data['detected_at']) 
                       if isinstance(data.get('detected_at'), str) 
                       else data.get('detected_at', datetime.utcnow())
        )
    
    def __repr__(self) -> str:
        return f"PhonemeError({self.error_type.value}, phoneme={self.phoneme}, severity={self.severity})"