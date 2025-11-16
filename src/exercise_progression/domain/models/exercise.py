# src/exercise_progression/domain/models/exercise.py

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import uuid

@dataclass
class Exercise:
    """
    Entidad Exercise adaptada a tu esquema.
    """
    id: uuid.UUID
    exercise_id: str  # "fonema_r_suave_1"
    order_index: int  # Posición en el camino lineal
    category: str  # "fonema", "ritmo", "entonacion"
    subcategory: Optional[str]  # "r_suave", "cortas", "preguntas"
    text_content: str  # Texto a pronunciar
    difficulty_level: int  # 1-5
    target_phonemes: List[str]  # ["r", "rr"]
    reference_audio_s3_url: str
    is_active: bool
    created_at: datetime
    
    def is_first_exercise(self) -> bool:
        """Retorna True si es el primer ejercicio"""
        return self.order_index == 1
    
    def get_previous_order_index(self) -> int:
        """Retorna el order_index del ejercicio anterior"""
        return self.order_index - 1
    
    def get_unlock_score_required(self) -> int:
        """Score mínimo para completar (siempre 70)"""
        return 70