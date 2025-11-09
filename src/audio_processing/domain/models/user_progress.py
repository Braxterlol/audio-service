"""
Entidad UserProgress - Representa el progreso agregado de un usuario.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class ProgressTrend(str, Enum):
    """Tendencia de progreso"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class ProblematicPhoneme:
    """Fonema problemático identificado"""
    phoneme: str
    error_rate: float  # 0-1
    attempts: int
    avg_severity: float  # 0-10
    
    def to_dict(self) -> dict:
        return {
            "phoneme": self.phoneme,
            "error_rate": round(self.error_rate, 2),
            "attempts": self.attempts,
            "avg_severity": round(self.avg_severity, 2)
        }


@dataclass
class UserProgress:
    """
    Entidad UserProgress - Representa el progreso agregado del usuario.
    
    Esta entidad se actualiza periódicamente y sirve para consultas rápidas
    de progreso sin tener que analizar todos los intentos.
    
    Attributes:
        user_id: UUID del usuario
        fonema_avg_score: Score promedio en ejercicios de fonemas
        ritmo_avg_score: Score promedio en ejercicios de ritmo
        entonacion_avg_score: Score promedio en ejercicios de entonación
        score_trend: Tendencia de los scores
        trend_percentage: Porcentaje de cambio en la tendencia
        problematic_phonemes: Lista de fonemas con dificultades
        strengths: Lista de fortalezas del usuario
        total_attempts: Total de intentos realizados
        successful_attempts: Intentos con score >= 70
        perfect_attempts: Intentos con score >= 95
        fonema_exercises_completed: Ejercicios de fonemas completados
        ritmo_exercises_completed: Ejercicios de ritmo completados
        entonacion_exercises_completed: Ejercicios de entonación completados
        user_cluster_id: ID del cluster ML al que pertenece
        cluster_profile: Perfil del cluster
        first_attempt_at: Fecha del primer intento
        last_attempt_at: Fecha del último intento
        last_updated: Última actualización del progreso
    """
    
    user_id: str
    
    # Promedios por categoría
    fonema_avg_score: Optional[float] = None
    ritmo_avg_score: Optional[float] = None
    entonacion_avg_score: Optional[float] = None
    
    # Tendencias
    score_trend: ProgressTrend = ProgressTrend.INSUFFICIENT_DATA
    trend_percentage: float = 0.0  # % de cambio
    
    # Fonemas problemáticos (top 5)
    problematic_phonemes: List[ProblematicPhoneme] = field(default_factory=list)
    
    # Fortalezas
    strengths: List[str] = field(default_factory=list)  # ["entonacion", "ritmo"]
    
    # Estadísticas generales
    total_attempts: int = 0
    successful_attempts: int = 0  # score >= 70
    perfect_attempts: int = 0  # score >= 95
    
    # Ejercicios completados por categoría
    fonema_exercises_completed: int = 0
    ritmo_exercises_completed: int = 0
    entonacion_exercises_completed: int = 0
    
    # Cluster ML (calculado por ML Analysis Service)
    user_cluster_id: Optional[int] = None
    cluster_profile: str = ""
    
    # Timestamps
    first_attempt_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # ========================================
    # MÉTODOS DE NEGOCIO
    # ========================================
    
    def get_overall_avg_score(self) -> float:
        """Calcula el score promedio general"""
        scores = []
        if self.fonema_avg_score is not None:
            scores.append(self.fonema_avg_score)
        if self.ritmo_avg_score is not None:
            scores.append(self.ritmo_avg_score)
        if self.entonacion_avg_score is not None:
            scores.append(self.entonacion_avg_score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def get_success_rate(self) -> float:
        """Calcula la tasa de éxito (%)"""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_attempts / self.total_attempts) * 100
    
    def get_perfect_rate(self) -> float:
        """Calcula la tasa de intentos perfectos (%)"""
        if self.total_attempts == 0:
            return 0.0
        return (self.perfect_attempts / self.total_attempts) * 100
    
    def is_improving(self) -> bool:
        """Verifica si está mejorando"""
        return self.score_trend == ProgressTrend.IMPROVING
    
    def is_declining(self) -> bool:
        """Verifica si está declinando"""
        return self.score_trend == ProgressTrend.DECLINING
    
    def has_sufficient_data(self) -> bool:
        """Verifica si tiene suficientes datos para análisis"""
        return self.total_attempts >= 10
    
    def get_weakest_category(self) -> Optional[str]:
        """Identifica la categoría más débil"""
        scores = {}
        
        if self.fonema_avg_score is not None:
            scores['fonema'] = self.fonema_avg_score
        if self.ritmo_avg_score is not None:
            scores['ritmo'] = self.ritmo_avg_score
        if self.entonacion_avg_score is not None:
            scores['entonacion'] = self.entonacion_avg_score
        
        if not scores:
            return None
        
        return min(scores, key=scores.get)
    
    def get_strongest_category(self) -> Optional[str]:
        """Identifica la categoría más fuerte"""
        scores = {}
        
        if self.fonema_avg_score is not None:
            scores['fonema'] = self.fonema_avg_score
        if self.ritmo_avg_score is not None:
            scores['ritmo'] = self.ritmo_avg_score
        if self.entonacion_avg_score is not None:
            scores['entonacion'] = self.entonacion_avg_score
        
        if not scores:
            return None
        
        return max(scores, key=scores.get)
    
    def get_top_problematic_phonemes(self, limit: int = 3) -> List[ProblematicPhoneme]:
        """Obtiene los N fonemas más problemáticos"""
        sorted_phonemes = sorted(
            self.problematic_phonemes,
            key=lambda p: p.error_rate,
            reverse=True
        )
        return sorted_phonemes[:limit]
    
    def add_problematic_phoneme(
        self,
        phoneme: str,
        error_rate: float,
        attempts: int,
        avg_severity: float
    ):
        """Agrega o actualiza un fonema problemático"""
        # Buscar si ya existe
        for i, p in enumerate(self.problematic_phonemes):
            if p.phoneme == phoneme:
                # Actualizar existente
                self.problematic_phonemes[i] = ProblematicPhoneme(
                    phoneme=phoneme,
                    error_rate=error_rate,
                    attempts=attempts,
                    avg_severity=avg_severity
                )
                return
        
        # Agregar nuevo
        self.problematic_phonemes.append(
            ProblematicPhoneme(
                phoneme=phoneme,
                error_rate=error_rate,
                attempts=attempts,
                avg_severity=avg_severity
            )
        )
        
        # Mantener solo top 5
        self.problematic_phonemes = sorted(
            self.problematic_phonemes,
            key=lambda p: p.error_rate,
            reverse=True
        )[:5]
    
    def update_trend(self, trend: ProgressTrend, percentage: float):
        """Actualiza la tendencia de progreso"""
        self.score_trend = trend
        self.trend_percentage = percentage
    
    def update_cluster(self, cluster_id: int, profile: str):
        """Actualiza el cluster ML"""
        self.user_cluster_id = cluster_id
        self.cluster_profile = profile
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para PostgreSQL"""
        return {
            "user_id": self.user_id,
            "fonema_avg_score": round(self.fonema_avg_score, 2) if self.fonema_avg_score else None,
            "ritmo_avg_score": round(self.ritmo_avg_score, 2) if self.ritmo_avg_score else None,
            "entonacion_avg_score": round(self.entonacion_avg_score, 2) if self.entonacion_avg_score else None,
            "score_trend": self.score_trend.value,
            "trend_percentage": round(self.trend_percentage, 2),
            "problematic_phonemes": [p.to_dict() for p in self.problematic_phonemes],
            "strengths": self.strengths,
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "perfect_attempts": self.perfect_attempts,
            "fonema_exercises_completed": self.fonema_exercises_completed,
            "ritmo_exercises_completed": self.ritmo_exercises_completed,
            "entonacion_exercises_completed": self.entonacion_exercises_completed,
            "user_cluster_id": self.user_cluster_id,
            "cluster_profile": self.cluster_profile,
            "first_attempt_at": self.first_attempt_at.isoformat() if self.first_attempt_at else None,
            "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProgress':
        """Crea instancia desde diccionario"""
        return cls(
            user_id=data['user_id'],
            fonema_avg_score=data.get('fonema_avg_score'),
            ritmo_avg_score=data.get('ritmo_avg_score'),
            entonacion_avg_score=data.get('entonacion_avg_score'),
            score_trend=ProgressTrend(data.get('score_trend', 'insufficient_data')),
            trend_percentage=data.get('trend_percentage', 0.0),
            problematic_phonemes=[
                ProblematicPhoneme(**p) for p in data.get('problematic_phonemes', [])
            ],
            strengths=data.get('strengths', []),
            total_attempts=data.get('total_attempts', 0),
            successful_attempts=data.get('successful_attempts', 0),
            perfect_attempts=data.get('perfect_attempts', 0),
            fonema_exercises_completed=data.get('fonema_exercises_completed', 0),
            ritmo_exercises_completed=data.get('ritmo_exercises_completed', 0),
            entonacion_exercises_completed=data.get('entonacion_exercises_completed', 0),
            user_cluster_id=data.get('user_cluster_id'),
            cluster_profile=data.get('cluster_profile', ''),
            first_attempt_at=datetime.fromisoformat(data['first_attempt_at']) 
                           if data.get('first_attempt_at') else None,
            last_attempt_at=datetime.fromisoformat(data['last_attempt_at']) 
                          if data.get('last_attempt_at') else None,
            last_updated=datetime.fromisoformat(data['last_updated']) 
                        if isinstance(data.get('last_updated'), str) 
                        else data.get('last_updated', datetime.utcnow())
        )
    
    def __repr__(self) -> str:
        overall = self.get_overall_avg_score()
        return (
            f"UserProgress(user_id={self.user_id[:8]}..., "
            f"avg_score={overall:.1f}, "
            f"attempts={self.total_attempts}, "
            f"trend={self.score_trend.value})"
        )