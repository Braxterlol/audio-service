"""
ValidationService - Servicio para validaciones de negocio.
"""

from typing import Optional
from src.audio_processing.domain.repositories.attempt_repository import AttemptRepository
from src.exercises.domain.repositories.exercise_repository import ExerciseRepository


class ValidationService:
    """
    Servicio de validación de reglas de negocio.
    """
    
    def __init__(
        self,
        attempt_repository: AttemptRepository,
        exercise_repository: ExerciseRepository
    ):
        self.attempt_repository = attempt_repository
        self.exercise_repository = exercise_repository
    
    async def can_user_attempt_exercise(
        self,
        user_id: str,
        exercise_id: str,
        daily_limit: Optional[int] = None
    ) -> tuple[bool, str]:
        """
        Valida si el usuario puede intentar un ejercicio.
        
        Args:
            user_id: UUID del usuario
            exercise_id: ID del ejercicio
            daily_limit: Límite diario de ejercicios (None = ilimitado)
        
        Returns:
            tuple: (puede_intentar, mensaje_error)
        """
        # 1. Verificar que el ejercicio existe y está activo
        exercise = await self.exercise_repository.find_by_exercise_id(exercise_id)
        if not exercise:
            return False, "Ejercicio no encontrado"
        
        if not exercise.is_active:
            return False, "Este ejercicio no está disponible"
        
        # 2. Verificar límite diario (si aplica)
        if daily_limit is not None:
            # Contar intentos de hoy
            from datetime import datetime, timedelta
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            recent_attempts = await self.attempt_repository.find_recent_by_user(
                user_id,
                days=1
            )
            
            # Filtrar solo los de hoy
            today_attempts = [
                a for a in recent_attempts
                if a.attempted_at >= today_start
            ]
            
            if len(today_attempts) >= daily_limit:
                return False, f"Has alcanzado tu límite diario de {daily_limit} ejercicios"
        
        # 3. Todas las validaciones pasaron
        return True, ""
    
    async def validate_attempt_ownership(
        self,
        attempt_id: str,
        user_id: str
    ) -> tuple[bool, str]:
        """
        Valida que el intento pertenezca al usuario.
        
        Args:
            attempt_id: UUID del intento
            user_id: UUID del usuario
        
        Returns:
            tuple: (es_propietario, mensaje_error)
        """
        attempt = await self.attempt_repository.find_by_id(attempt_id)
        
        if not attempt:
            return False, "Intento no encontrado"
        
        if attempt.user_id != user_id:
            return False, "No tienes permiso para acceder a este intento"
        
        return True, ""
    
    async def validate_exercise_prerequisites(
        self,
        user_id: str,
        exercise_id: str
    ) -> tuple[bool, str]:
        """
        Valida que el usuario cumpla prerequisitos para un ejercicio.
        (Opcional: para ejercicios avanzados que requieren completar básicos)
        
        Args:
            user_id: UUID del usuario
            exercise_id: ID del ejercicio
        
        Returns:
            tuple: (cumple_requisitos, mensaje_error)
        """
        # TODO: Implementar lógica de prerequisitos si es necesario
        # Por ahora, todos los ejercicios son accesibles
        return True, ""

