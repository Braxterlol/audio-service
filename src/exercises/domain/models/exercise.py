from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class ExerciseCategory(str, Enum):
    """Categorías de ejercicios"""
    FONEMA = "fonema"
    RITMO = "ritmo"
    ENTONACION = "entonacion"


class DifficultyLevel(int, Enum):
    """Niveles de dificultad"""
    MUY_FACIL = 1
    FACIL = 2
    MEDIO = 3
    DIFICIL = 4
    MUY_DIFICIL = 5


@dataclass
class Exercise:
    """
    Entidad Exercise - Modelo de dominio para ejercicios fonéticos.
    
    Attributes:
        id: Identificador único (UUID de la BD)
        exercise_id: Identificador del ejercicio (ej: "fonema_r_suave_1")
        category: Categoría del ejercicio
        subcategory: Subcategoría específica (ej: "r_suave", "pregunta")
        text_content: Texto que el usuario debe pronunciar
        difficulty_level: Nivel de dificultad (1-5)
        target_phonemes: Lista de fonemas objetivo
        reference_audio_url: URL del audio de referencia en S3
        instructions: Instrucciones opcionales para el usuario
        tips: Consejos opcionales
        is_active: Si el ejercicio está activo
        created_at: Fecha de creación
    """
    
    # Identificadores
    id: str
    exercise_id: str
    
    # Clasificación
    category: ExerciseCategory
    subcategory: str
    
    # Contenido
    text_content: str
    difficulty_level: DifficultyLevel
    
    # Referencias
    reference_audio_url: str
    
    # Listas con valores por defecto
    target_phonemes: List[str] = field(default_factory=list)
    
    # Metadata
    instructions: Optional[str] = None
    tips: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validaciones del dominio"""
        self._validate_text_content()
        self._validate_exercise_id()
        self._validate_reference_url()
    
    def _validate_text_content(self):
        """Validar que el texto no esté vacío"""
        if not self.text_content or not self.text_content.strip():
            raise ValueError("El texto del ejercicio no puede estar vacío")
        
        if len(self.text_content) > 500:
            raise ValueError("El texto del ejercicio no puede exceder 500 caracteres")
    
    def _validate_exercise_id(self):
        """Validar formato del exercise_id"""
        if not self.exercise_id or not self.exercise_id.strip():
            raise ValueError("El exercise_id no puede estar vacío")
        
        # Debe tener formato: categoria_subcategoria_numero
        parts = self.exercise_id.split('_')
        if len(parts) < 3:
            raise ValueError(
                f"El exercise_id debe tener formato 'categoria_subcategoria_numero', "
                f"recibido: {self.exercise_id}"
            )
    
    def _validate_reference_url(self):
        """Validar que la URL de referencia sea válida"""
        if not self.reference_audio_url:
            raise ValueError("La URL del audio de referencia es obligatoria")
        
        if not (self.reference_audio_url.startswith('http://') or 
                self.reference_audio_url.startswith('https://')):
            raise ValueError("La URL del audio de referencia debe ser válida (http/https)")
    
    # ========================================
    # MÉTODOS DE NEGOCIO (Domain Logic)
    # ========================================
    
    def is_phoneme_exercise(self) -> bool:
        """Verifica si es un ejercicio de fonemas"""
        return self.category == ExerciseCategory.FONEMA
    
    def is_rhythm_exercise(self) -> bool:
        """Verifica si es un ejercicio de ritmo"""
        return self.category == ExerciseCategory.RITMO
    
    def is_intonation_exercise(self) -> bool:
        """Verifica si es un ejercicio de entonación"""
        return self.category == ExerciseCategory.ENTONACION
    
    def has_target_phonemes(self) -> bool:
        """Verifica si tiene fonemas objetivo definidos"""
        return len(self.target_phonemes) > 0
    
    def get_expected_duration_range(self) -> tuple[float, float]:
        """
        Retorna el rango de duración esperada según el tipo de ejercicio.
        
        Returns:
            tuple: (duración_mínima, duración_máxima) en segundos
        """
        if self.is_phoneme_exercise():
            # Palabras individuales: 0.5-2 segundos
            return (0.5, 2.0)
        elif self.is_rhythm_exercise():
            # Frases: 2-8 segundos según longitud
            word_count = len(self.text_content.split())
            if word_count <= 6:
                return (2.0, 4.0)  # Frases cortas
            else:
                return (4.0, 8.0)  # Frases largas
        else:  # Entonación
            # Similar a ritmo pero puede ser más corto
            return (1.0, 5.0)
    
    def is_suitable_for_difficulty_level(self, user_level: str) -> bool:
        """
        Determina si el ejercicio es adecuado para el nivel del usuario.
        
        Args:
            user_level: Nivel del usuario ('principiante', 'intermedio', 'avanzado')
        
        Returns:
            bool: True si es adecuado
        """
        level_mapping = {
            'principiante': [1, 2],
            'intermedio': [2, 3],
            'avanzado': [3, 4, 5]
        }
        
        return self.difficulty_level.value in level_mapping.get(user_level, [1, 2])
    
    def deactivate(self):
        """Desactiva el ejercicio (soft delete)"""
        self.is_active = False
    
    def activate(self):
        """Activa el ejercicio"""
        self.is_active = True
    
    def update_content(self, new_text: str):
        """
        Actualiza el texto del ejercicio.
        
        Args:
            new_text: Nuevo texto
        
        Raises:
            ValueError: Si el nuevo texto no es válido
        """
        if not new_text or not new_text.strip():
            raise ValueError("El nuevo texto no puede estar vacío")
        
        if len(new_text) > 500:
            raise ValueError("El texto no puede exceder 500 caracteres")
        
        self.text_content = new_text.strip()
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario (para serialización)"""
        return {
            "id": self.id,
            "exercise_id": self.exercise_id,
            "category": self.category.value,
            "subcategory": self.subcategory,
            "text_content": self.text_content,
            "difficulty_level": self.difficulty_level.value,
            "target_phonemes": self.target_phonemes,
            "reference_audio_url": self.reference_audio_url,
            "instructions": self.instructions,
            "tips": self.tips,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Exercise':
        """
        Crea una instancia de Exercise desde un diccionario.
        
        Args:
            data: Diccionario con los datos del ejercicio
        
        Returns:
            Exercise: Nueva instancia
        """
        return cls(
            id=data['id'],
            exercise_id=data['exercise_id'],
            category=ExerciseCategory(data['category']),
            subcategory=data['subcategory'],
            text_content=data['text_content'],
            difficulty_level=DifficultyLevel(data['difficulty_level']),
            target_phonemes=data.get('target_phonemes', []),
            reference_audio_url=data['reference_audio_url'],
            instructions=data.get('instructions'),
            tips=data.get('tips'),
            is_active=data.get('is_active', True),
            created_at=datetime.fromisoformat(data['created_at']) 
                       if isinstance(data.get('created_at'), str) 
                       else data.get('created_at', datetime.utcnow())
        )
    
    def __repr__(self) -> str:
        return (
            f"Exercise(id={self.id}, exercise_id={self.exercise_id}, "
            f"category={self.category.value}, text='{self.text_content}')"
        )
    
    def __eq__(self, other) -> bool:
        """Dos ejercicios son iguales si tienen el mismo ID"""
        if not isinstance(other, Exercise):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Permite usar Exercise en sets y como key en dicts"""
        return hash(self.id)