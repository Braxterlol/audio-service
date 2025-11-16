# src/exercise_progression/domain/models/user_exercise_progress.py

from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import uuid

@dataclass
class UserExerciseProgress:
    """
    Progreso del usuario en un ejercicio.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    exercise_id: uuid.UUID  # FK a exercises.id
    status: str  # "locked", "available", "in_progress", "completed"
    best_score: Optional[float]
    attempts_count: int
    last_attempt_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    def calculate_stars(self) -> int:
        """
        Calcula estrellas basado en best_score.
        0-69: 0 estrellas (no completado)
        70-79: 1 estrella
        80-89: 2 estrellas
        90+: 3 estrellas
        """
        if self.best_score is None or self.best_score < 70:
            return 0
        elif self.best_score < 80:
            return 1
        elif self.best_score < 90:
            return 2
        else:
            return 3
    
    def is_completed(self) -> bool:
        """Retorna True si está completado"""
        return self.status in ["completed", "mastered"]
    
    def is_locked(self) -> bool:
        """Retorna True si está bloqueado"""
        return self.status == "locked"
    
    def update_from_attempt(self, overall_score: float) -> None:
        """
        Actualiza el progreso después de un intento.
        
        Args:
            overall_score: Score del intento actual
        """
        from datetime import datetime
        
        # Incrementar intentos
        self.attempts_count += 1
        self.last_attempt_at = datetime.utcnow()
        
        # Actualizar best_score
        if self.best_score is None or overall_score > self.best_score:
            self.best_score = overall_score
        
        # Actualizar status
        if overall_score >= 70:
            if self.status != "completed":
                self.completed_at = datetime.utcnow()
            
            if overall_score >= 90:
                self.status = "mastered"
            else:
                self.status = "completed"
        else:
            if self.status == "locked" or self.status == "available":
                self.status = "in_progress"
        
        self.updated_at = datetime.utcnow()