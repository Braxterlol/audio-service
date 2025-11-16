# src/exercise_progression/infrastructure/helpers/dependencies.py

from functools import lru_cache
from src.db.postgres import postgres_db
from src.exercise_progression.infrastructure.repositories.postgres_exercise_repository import PostgresExerciseRepository
from src.exercise_progression.infrastructure.repositories.postgres_user_exercise_progress_repository import PostgresUserExerciseProgressRepository
from src.exercise_progression.application.services.exercise_progression_service import ExerciseProgressionService
from src.exercise_progression.application.use_cases.get_exercise_map_use_case import GetExerciseMapUseCase
from src.exercise_progression.application.use_cases.get_exercise_details_use_case import GetExerciseDetailsUseCase
from src.exercise_progression.application.use_cases.validate_exercise_access_use_case import ValidateExerciseAccessUseCase
from src.exercise_progression.infrastructure.controllers.exercise_controller import ExerciseController


def get_exercise_repository() -> PostgresExerciseRepository:
    """Retorna instancia de ExerciseRepository"""
    pool = postgres_db.get_pool()
    return PostgresExerciseRepository(pool)


def get_progress_repository() -> PostgresUserExerciseProgressRepository:
    """Retorna instancia de UserExerciseProgressRepository"""
    pool = postgres_db.get_pool()
    return PostgresUserExerciseProgressRepository(pool)


def get_exercise_progression_service() -> ExerciseProgressionService:
    """Retorna instancia de ExerciseProgressionService"""
    return ExerciseProgressionService(
        exercise_repo=get_exercise_repository(),
        progress_repo=get_progress_repository()
    )


def get_exercise_controller() -> ExerciseController:
    """
    Retorna instancia de ExerciseController.
    
    IMPORTANTE: Crea instancias NUEVAS en cada llamada.
    """
    progression_service = get_exercise_progression_service()
    exercise_repo = get_exercise_repository()
    progress_repo = get_progress_repository()
    
    return ExerciseController(
        get_map_use_case=GetExerciseMapUseCase(progression_service),
        get_details_use_case=GetExerciseDetailsUseCase(exercise_repo, progress_repo),
        validate_access_use_case=ValidateExerciseAccessUseCase(progression_service)
    )