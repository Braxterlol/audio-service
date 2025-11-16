# src/exercise_progression/application/services/exercise_progression_service.py

from typing import Dict, List, Optional
import uuid
from src.exercise_progression.domain.repositories.exercise_repository import ExerciseRepository
from src.exercise_progression.domain.repositories.user_exercise_progress_repository import UserExerciseProgressRepository
from src.exercise_progression.domain.models.exercise import Exercise
from src.exercise_progression.domain.models.user_exercise_progress import UserExerciseProgress

class ExerciseProgressionService:
    
    def __init__(
        self,
        exercise_repo: ExerciseRepository,
        progress_repo: UserExerciseProgressRepository
    ):
        self.exercise_repo = exercise_repo
        self.progress_repo = progress_repo
    
    async def get_user_exercise_map(self, user_id: uuid.UUID) -> Dict:
        # 1. Obtener datos
        exercises = await self.exercise_repo.get_all_ordered()
        progress_list = await self.progress_repo.get_all_by_user(user_id)
        
        # 2. Crear mapa de progreso por exercise_id
        progress_map = {p.exercise_id: p for p in progress_list}
        
        # 3. Agrupar por categoría
        categories = self._group_by_category(exercises, progress_map)
        
        # 4. Encontrar ejercicio actual
        current_index = self._find_current_exercise_index(exercises, progress_map)
        
        # 5. Calcular estadísticas totales
        total_completed = sum(1 for p in progress_list if p.is_completed())
        total_stars = sum(p.calculate_stars() for p in progress_list if p.is_completed())
        
        return {
            "total_exercises": len(exercises),
            "completed_exercises": total_completed,
            "total_stars": total_stars,
            "current_exercise_index": current_index,
            "categories": categories
        }
    
    def _group_by_category(
        self, 
        exercises: List[Exercise], 
        progress_map: Dict[uuid.UUID, UserExerciseProgress]
    ) -> List[Dict]:
        """Agrupa ejercicios por categoría"""
        categories = {}
        
        for exercise in exercises:
            if exercise.category not in categories:
                categories[exercise.category] = {
                    "name": self._get_category_display_name(exercise.category),
                    "category": exercise.category,
                    "total": 0,
                    "completed": 0,
                    "total_stars": 0,
                    "exercises": []
                }
            
            # Obtener progreso
            progress = progress_map.get(exercise.id)
            
            # ✅ USAR EL STATUS DEL PROGRESO DIRECTAMENTE
            # No recalcular, confiar en lo que está en la DB
            status = progress.status if progress else "locked"
            
            # Construir datos del ejercicio
            exercise_data = {
                "id": str(exercise.id),
                "exercise_id": exercise.exercise_id,
                "order_index": exercise.order_index,
                "title": self._get_exercise_title(exercise),
                "category": exercise.category,
                "subcategory": exercise.subcategory,
                "difficulty_level": exercise.difficulty_level,
                "text_content": exercise.text_content,
                "status": status,  # ✅ Usar directamente
                "best_score": progress.best_score if progress else None,
                "stars": progress.calculate_stars() if progress else 0,
                "attempts": progress.attempts_count if progress else 0,
                "completed_at": progress.completed_at.isoformat() if progress and progress.completed_at else None
            }
            
            # Agregar a categoría
            categories[exercise.category]["exercises"].append(exercise_data)
            categories[exercise.category]["total"] += 1
            
            if progress and progress.is_completed():
                categories[exercise.category]["completed"] += 1
                categories[exercise.category]["total_stars"] += progress.calculate_stars()
        
        return list(categories.values())
    
    def _get_category_display_name(self, category: str) -> str:
        """Retorna nombre legible de categoría"""
        names = {
            "fonema": "Fonemas",
            "ritmo": "Ritmo",
            "entonacion": "Entonación"
        }
        return names.get(category, category.title())
    
    def _get_exercise_title(self, exercise: Exercise) -> str:
        """Genera título legible del ejercicio"""
        # Ejemplo: "R Suave - cara"
        if exercise.subcategory:
            subcategory_title = exercise.subcategory.replace("_", " ").title()
            return f"{subcategory_title} - {exercise.text_content}"
        return exercise.text_content
    
    def _find_current_exercise_index(
        self, 
        exercises: List[Exercise], 
        progress_map: Dict[uuid.UUID, UserExerciseProgress]
    ) -> int:
        """Encuentra el índice del ejercicio actual (primer disponible no completado)"""
        for exercise in exercises:
            progress = progress_map.get(exercise.id)
            if not progress or progress.status in ["available", "in_progress"]:
                return exercise.order_index
        
        # Si completó todos, retornar el último
        return exercises[-1].order_index if exercises else 0
    
    async def can_access_exercise(
        self, 
        user_id: uuid.UUID, 
        exercise_id: uuid.UUID
    ) -> bool:
        """
        Valida si el usuario puede acceder a un ejercicio.
        
        Reglas:
        - Ejercicio con order_index = 1: siempre True
        - Cualquier otro: el anterior debe estar completado (score >= 70)
        """
        exercise = await self.exercise_repo.get_by_id(exercise_id)
        if not exercise:
            return False
        
        # Primer ejercicio siempre disponible
        if exercise.is_first_exercise():
            return True
        
        # Obtener ejercicio anterior
        previous_exercise = await self.exercise_repo.get_by_order_index(
            exercise.get_previous_order_index()
        )
        
        if not previous_exercise:
            return False
        
        # Verificar progreso del anterior
        previous_progress = await self.progress_repo.get_by_user_and_exercise(
            user_id, previous_exercise.id
        )
        
        # Si el anterior está completado → True
        return previous_progress and previous_progress.is_completed()
    
    async def record_attempt(
        self, 
        user_id: uuid.UUID, 
        exercise_id: uuid.UUID, 
        overall_score: float
    ) -> Dict:
        """
        Registra un intento y actualiza progreso.
        
        Returns:
            Dict con info de progreso actualizado y siguiente ejercicio desbloqueado
        """
        # 1. Obtener o crear progreso
        progress = await self.progress_repo.get_by_user_and_exercise(user_id, exercise_id)
        
        if not progress:
            # Crear nuevo progreso
            progress = UserExerciseProgress(
                id=uuid.uuid4(),
                user_id=user_id,
                exercise_id=exercise_id,
                status="in_progress",
                best_score=None,
                attempts_count=0,
                last_attempt_at=None,
                completed_at=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        
        # 2. Actualizar desde intento
        was_completed_before = progress.is_completed()
        progress.update_from_attempt(overall_score)
        
        # 3. Guardar
        await self.progress_repo.save(progress)
        
        # 4. Si se completó por primera vez, desbloquear siguiente
        unlocked_next = False
        next_exercise = None
        
        if progress.is_completed() and not was_completed_before:
            exercise = await self.exercise_repo.get_by_id(exercise_id)
            next_exercise_entity = await self.exercise_repo.get_by_order_index(
                exercise.order_index + 1
            )
            
            if next_exercise_entity:
                await self.progress_repo.unlock_exercise(user_id, next_exercise_entity.id)
                unlocked_next = True
                next_exercise = {
                    "exercise_id": next_exercise_entity.exercise_id,
                    "title": self._get_exercise_title(next_exercise_entity),
                    "order_index": next_exercise_entity.order_index,
                    "category": next_exercise_entity.category
                }
        
        return {
            "progress_updated": True,
            "status": progress.status,
            "stars_earned": progress.calculate_stars(),
            "best_score": progress.best_score,
            "unlocked_next": unlocked_next,
            "next_exercise": next_exercise
        }
    
    async def initialize_new_user(self, user_id: uuid.UUID) -> None:
        """Inicializa progreso para usuario nuevo"""
        await self.progress_repo.initialize_user_progress(user_id)