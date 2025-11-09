"""
UserExerciseProgress - Modelo de dominio para el progreso del usuario en ejercicios.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ProgressStatus(Enum):
    """Estados posibles del progreso en un ejercicio"""
    LOCKED = "locked"  # Bloqueado, no disponible aún
    UNLOCKED = "unlocked"  # Desbloqueado, disponible para intentar
    IN_PROGRESS = "in_progress"  # Comenzado pero no completado
    COMPLETED = "completed"  # Completado con score aprobatorio
    MASTERED = "mastered"  # Dominado (score perfecto o muy alto)


@dataclass
class UserExerciseProgress:
    """
    Entidad de dominio que representa el progreso de un usuario en un ejercicio.
    """
    
    id: str
    user_id: str
    exercise_id: str
    status: ProgressStatus
    best_score: Optional[float] = None
    attempts_count: int = 0
    last_attempt_at: Optional[datetime] = None
    unlocked_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    @property
    def is_available(self) -> bool:
        """Verifica si el ejercicio está disponible para intentar."""
        return self.status in [
            ProgressStatus.UNLOCKED,
            ProgressStatus.IN_PROGRESS,
            ProgressStatus.COMPLETED,
            ProgressStatus.MASTERED
        ]
    
    @property
    def is_completed(self) -> bool:
        """Verifica si el ejercicio fue completado."""
        return self.status in [ProgressStatus.COMPLETED, ProgressStatus.MASTERED]
    
    def mark_as_in_progress(self):
        """Marca el ejercicio como en progreso."""
        if self.status == ProgressStatus.UNLOCKED:
            self.status = ProgressStatus.IN_PROGRESS
            self.updated_at = datetime.utcnow()
    
    def update_score(self, new_score: float, passing_score: float = 70.0):
        """
        Actualiza el mejor score y el estado según el nuevo intento.
        
        Args:
            new_score: Score del nuevo intento
            passing_score: Score mínimo para aprobar
        """
        # Actualizar mejor score
        if self.best_score is None or new_score > self.best_score:
            self.best_score = new_score
        
        # Actualizar contador
        self.attempts_count += 1
        self.last_attempt_at = datetime.utcnow()
        
        # Actualizar estado
        if new_score >= 95.0:
            self.status = ProgressStatus.MASTERED
            if not self.completed_at:
                self.completed_at = datetime.utcnow()
        elif new_score >= passing_score:
            if self.status != ProgressStatus.MASTERED:
                self.status = ProgressStatus.COMPLETED
            if not self.completed_at:
                self.completed_at = datetime.utcnow()
        else:
            if self.status == ProgressStatus.UNLOCKED:
                self.status = ProgressStatus.IN_PROGRESS
        
        self.updated_at = datetime.utcnow()
    
    def unlock(self):
        """Desbloquea el ejercicio."""
        if self.status == ProgressStatus.LOCKED:
            self.status = ProgressStatus.UNLOCKED
            self.unlocked_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convierte a diccionario para respuestas JSON."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "exercise_id": self.exercise_id,
            "status": self.status.value,
            "best_score": round(self.best_score, 2) if self.best_score else None,
            "attempts_count": self.attempts_count,
            "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "is_available": self.is_available,
            "is_completed": self.is_completed
        }