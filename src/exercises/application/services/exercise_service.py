"""
ExerciseService - Servicio de aplicación para lógica de negocio de ejercicios.

Coordina operaciones complejas que involucran múltiples repositorios
o lógica de negocio que no pertenece directamente a las entidades.
"""

from typing import List, Optional, Dict
from src.exercises.domain.models.exercise import Exercise, ExerciseCategory
from src.exercises.domain.models.reference_features import ReferenceFeatures
from src.exercises.domain.repositories.exercise_repository import ExerciseRepository
from src.exercises.domain.repositories.reference_features_repository import ReferenceFeaturesRepository


class ExerciseService:
    """
    Servicio de aplicación para operaciones de negocio con ejercicios.
    """
    
    def __init__(
        self,
        exercise_repository: ExerciseRepository,
        reference_features_repository: ReferenceFeaturesRepository
    ):
        self.exercise_repository = exercise_repository
        self.reference_features_repository = reference_features_repository
    
    async def get_exercises_with_features_status(
        self,
        category: Optional[ExerciseCategory] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Obtiene ejercicios con información de si tienen features precalculadas.
        
        Args:
            category: Filtrar por categoría
            limit: Límite de resultados
            offset: Offset para paginación
        
        Returns:
            List[Dict]: Ejercicios con flag has_reference_features
        """
        exercises = await self.exercise_repository.find_all(
            category=category,
            limit=limit,
            offset=offset
        )
        
        result = []
        for exercise in exercises:
            has_features = await self.reference_features_repository.exists(
                exercise.exercise_id
            )
            
            exercise_dict = exercise.to_dict()
            exercise_dict['has_reference_features'] = has_features
            result.append(exercise_dict)
        
        return result
    
    async def get_exercises_by_difficulty_range(
        self,
        min_difficulty: int,
        max_difficulty: int,
        category: Optional[ExerciseCategory] = None
    ) -> List[Exercise]:
        """
        Obtiene ejercicios dentro de un rango de dificultad.
        
        Args:
            min_difficulty: Dificultad mínima (1-5)
            max_difficulty: Dificultad máxima (1-5)
            category: Categoría opcional
        
        Returns:
            List[Exercise]: Ejercicios en el rango
        """
        all_exercises = await self.exercise_repository.find_all(
            category=category,
            limit=100  # Asumiendo que no hay más de 100 ejercicios
        )
        
        return [
            ex for ex in all_exercises
            if min_difficulty <= ex.difficulty_level.value <= max_difficulty
        ]
    
    async def get_exercises_for_user_level(
        self,
        user_level: str,
        category: Optional[ExerciseCategory] = None
    ) -> List[Exercise]:
        """
        Obtiene ejercicios adecuados para el nivel del usuario.
        
        Args:
            user_level: Nivel del usuario ('principiante', 'intermedio', 'avanzado')
            category: Categoría opcional
        
        Returns:
            List[Exercise]: Ejercicios recomendados
        """
        all_exercises = await self.exercise_repository.find_all(
            category=category,
            limit=100
        )
        
        return [
            ex for ex in all_exercises
            if ex.is_suitable_for_difficulty_level(user_level)
        ]
    
    async def get_exercises_grouped_by_subcategory(
        self,
        category: ExerciseCategory
    ) -> Dict[str, List[Exercise]]:
        """
        Obtiene ejercicios agrupados por subcategoría.
        
        Args:
            category: Categoría a agrupar
        
        Returns:
            Dict: {subcategoria: [ejercicios]}
        """
        return await self.exercise_repository.find_by_category_grouped(category)
    
    async def validate_exercise_has_features(
        self,
        exercise_id: str
    ) -> tuple[bool, Optional[str]]:
        """
        Valida que un ejercicio tenga features de referencia precalculadas.
        
        Args:
            exercise_id: ID del ejercicio
        
        Returns:
            tuple: (es_valido, mensaje_error)
        """
        # Verificar que el ejercicio existe
        exercise = await self.exercise_repository.find_by_exercise_id(exercise_id)
        if not exercise:
            return False, f"Ejercicio {exercise_id} no encontrado"
        
        # Verificar que está activo
        if not exercise.is_active:
            return False, f"Ejercicio {exercise_id} no está activo"
        
        # Verificar que tiene features
        has_features = await self.reference_features_repository.exists(exercise_id)
        if not has_features:
            return False, f"Ejercicio {exercise_id} no tiene features de referencia precalculadas"
        
        return True, None
    
    async def get_exercise_statistics(self) -> Dict:
        """
        Obtiene estadísticas generales de ejercicios.
        
        Returns:
            Dict: Estadísticas (total, por categoría, con/sin features)
        """
        # Total de ejercicios
        total = await self.exercise_repository.count()
        
        # Por categoría
        fonema_count = await self.exercise_repository.count(
            category=ExerciseCategory.FONEMA
        )
        ritmo_count = await self.exercise_repository.count(
            category=ExerciseCategory.RITMO
        )
        entonacion_count = await self.exercise_repository.count(
            category=ExerciseCategory.ENTONACION
        )
        
        # Con features precalculadas
        features_count = await self.reference_features_repository.count_cached()
        
        return {
            "total_exercises": total,
            "by_category": {
                "fonema": fonema_count,
                "ritmo": ritmo_count,
                "entonacion": entonacion_count
            },
            "with_reference_features": features_count,
            "missing_features": total - features_count,
            "completion_percentage": (features_count / total * 100) if total > 0 else 0
        }
    
    async def recommend_next_exercises(
        self,
        current_exercise_id: str,
        limit: int = 3
    ) -> List[Exercise]:
        """
        Recomienda ejercicios similares o de progresión natural.
        
        Args:
            current_exercise_id: ID del ejercicio actual
            limit: Número de recomendaciones
        
        Returns:
            List[Exercise]: Ejercicios recomendados
        """
        # Obtener ejercicio actual
        current = await self.exercise_repository.find_by_exercise_id(current_exercise_id)
        if not current:
            return []
        
        # Obtener ejercicios de la misma categoría
        same_category = await self.exercise_repository.find_all(
            category=current.category,
            limit=50
        )
        
        # Filtrar ejercicios:
        # 1. Misma subcategoría pero diferente ejercicio
        # 2. Dificultad similar (±1)
        recommendations = []
        
        for ex in same_category:
            if ex.id == current.id:
                continue
            
            # Preferir misma subcategoría
            if ex.subcategory == current.subcategory:
                recommendations.append((ex, 3))  # Alta prioridad
            # Dificultad similar
            elif abs(ex.difficulty_level.value - current.difficulty_level.value) <= 1:
                recommendations.append((ex, 2))  # Media prioridad
            # Mismo fonema objetivo
            elif current.has_target_phonemes() and ex.has_target_phonemes():
                if set(ex.target_phonemes) & set(current.target_phonemes):
                    recommendations.append((ex, 1))  # Baja prioridad
        
        # Ordenar por prioridad y retornar
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [ex for ex, _ in recommendations[:limit]]