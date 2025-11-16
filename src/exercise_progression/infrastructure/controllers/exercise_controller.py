# src/exercise_progression/infrastructure/controllers/exercise_controller.py

import uuid
import logging
from typing import Dict, Optional
from src.exercise_progression.application.use_cases.get_exercise_map_use_case import GetExerciseMapUseCase
from src.exercise_progression.application.use_cases.get_exercise_details_use_case import GetExerciseDetailsUseCase
from src.exercise_progression.application.use_cases.validate_exercise_access_use_case import ValidateExerciseAccessUseCase

logger = logging.getLogger(__name__)


class ExerciseController:
    """
    Controller para endpoints de ejercicios.
    """
    
    def __init__(
        self,
        get_map_use_case: GetExerciseMapUseCase,
        get_details_use_case: GetExerciseDetailsUseCase,
        validate_access_use_case: ValidateExerciseAccessUseCase
    ):
        self.get_map_use_case = get_map_use_case
        self.get_details_use_case = get_details_use_case
        self.validate_access_use_case = validate_access_use_case
    
    async def get_exercise_map(self, user_id: uuid.UUID) -> Dict:
        """
        Obtiene el mapa completo de ejercicios.
        """
        try:
            result = await self.get_map_use_case.execute(user_id)
            logger.info(f"✅ Mapa obtenido: {result['total_exercises']} ejercicios")
            return result
        except Exception as e:
            logger.error(f"❌ Error obteniendo mapa: {e}")
            raise
    
    async def get_exercise_details(
        self, 
        user_id: uuid.UUID, 
        exercise_id: str  # ← IMPORTANTE: exercise_id es STRING, no UUID
    ) -> Optional[Dict]:
        """
        Obtiene detalles de un ejercicio específico.
        
        Args:
            user_id: UUID del usuario
            exercise_id: exercise_id STRING (ej: "fonema_r_suave_1")
        """
        try:
            result = await self.get_details_use_case.execute(user_id, exercise_id)
            
            if result:
                logger.info(f"✅ Detalles obtenidos: {result['title']}")
            else:
                logger.warning(f"⚠️ Ejercicio no encontrado: {exercise_id}")
            
            return result
        except Exception as e:
            logger.error(f"❌ Error obteniendo detalles: {e}")
            raise
    
    async def validate_access(
        self, 
        user_id: uuid.UUID, 
        exercise_id: uuid.UUID  # ← Aquí SÍ es UUID
    ) -> bool:
        """
        Valida si el usuario puede acceder a un ejercicio.
        
        Args:
            user_id: UUID del usuario
            exercise_id: UUID del ejercicio (id de la tabla)
        """
        try:
            has_access = await self.validate_access_use_case.execute(user_id, exercise_id)
            
            if has_access:
                logger.info(f"✅ Usuario {user_id} tiene acceso")
            else:
                logger.warning(f"🔒 Usuario {user_id} NO tiene acceso")
            
            return has_access
        except Exception as e:
            logger.error(f"❌ Error validando acceso: {e}")
            raise