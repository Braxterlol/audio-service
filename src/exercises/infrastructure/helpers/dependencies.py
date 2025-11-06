"""
Dependencies - Inyección de dependencias para FastAPI.

Proporciona funciones para resolver dependencias de controladores,
repositorios y casos de uso.
"""

from typing import AsyncGenerator
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient
import asyncpg

# Importar repositorios
from src.exercises.infrastructure.data.postgres_exercise_repository import (
    PostgresExerciseRepository
)
from src.exercises.infrastructure.data.mongo_reference_features_repository import (
    MongoReferenceFeaturesRepository
)

# Importar casos de uso
from src.exercises.application.use_cases.get_exercises_use_case import (
    GetExercisesUseCase
)
from src.exercises.application.use_cases.get_exercise_by_id_use_case import (
    GetExerciseByIdUseCase,
    GetExerciseDetailsUseCase
)
from src.exercises.application.use_cases.get_reference_features_use_case import (
    GetReferenceFeaturesUseCase,
    GetReferenceFeaturesForComparisonUseCase
)

# Importar controladores
from src.exercises.infrastructure.controllers.exercise_controller import (
    ExerciseController,
    ExerciseHealthController
)


# ========================================
# DATABASE CONNECTIONS
# ========================================
# Estos serán inyectados desde la app principal
# Por ahora, definimos placeholders que deben ser configurados

_postgres_pool: asyncpg.Pool = None
_mongo_client: AsyncIOMotorClient = None


def set_postgres_pool(pool: asyncpg.Pool):
    """
    Configura el pool de PostgreSQL (llamar desde main.py al iniciar).
    
    Args:
        pool: Pool de conexiones asyncpg
    """
    global _postgres_pool
    _postgres_pool = pool


def set_mongo_client(client: AsyncIOMotorClient):
    """
    Configura el cliente de MongoDB (llamar desde main.py al iniciar).
    
    Args:
        client: Cliente de MongoDB motor
    """
    global _mongo_client
    _mongo_client = client


async def get_postgres_pool() -> asyncpg.Pool:
    """Obtiene el pool de PostgreSQL"""
    if _postgres_pool is None:
        raise RuntimeError("PostgreSQL pool no está configurado")
    return _postgres_pool


async def get_mongo_client() -> AsyncIOMotorClient:
    """Obtiene el cliente de MongoDB"""
    if _mongo_client is None:
        raise RuntimeError("MongoDB client no está configurado")
    return _mongo_client


# ========================================
# REPOSITORY DEPENDENCIES
# ========================================

async def get_exercise_repository(
    db_pool: asyncpg.Pool = Depends(get_postgres_pool)
) -> PostgresExerciseRepository:
    """
    Proporciona una instancia del repositorio de ejercicios.
    
    Returns:
        PostgresExerciseRepository: Repositorio de ejercicios
    """
    return PostgresExerciseRepository(db_pool)


async def get_reference_features_repository(
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client)
) -> MongoReferenceFeaturesRepository:
    """
    Proporciona una instancia del repositorio de features de referencia.
    
    Returns:
        MongoReferenceFeaturesRepository: Repositorio de features
    """
    return MongoReferenceFeaturesRepository(mongo_client)


# ========================================
# USE CASE DEPENDENCIES
# ========================================

async def get_exercises_use_case(
    exercise_repo = Depends(get_exercise_repository)
) -> GetExercisesUseCase:
    """Proporciona el caso de uso GetExercises"""
    return GetExercisesUseCase(exercise_repo)


async def get_exercise_by_id_use_case(
    exercise_repo = Depends(get_exercise_repository)
) -> GetExerciseByIdUseCase:
    """Proporciona el caso de uso GetExerciseById"""
    return GetExerciseByIdUseCase(exercise_repo)


async def get_exercise_details_use_case(
    exercise_repo = Depends(get_exercise_repository)
) -> GetExerciseDetailsUseCase:
    """Proporciona el caso de uso GetExerciseDetails"""
    return GetExerciseDetailsUseCase(exercise_repo)


async def get_reference_features_use_case(
    exercise_repo = Depends(get_exercise_repository),
    features_repo = Depends(get_reference_features_repository)
) -> GetReferenceFeaturesUseCase:
    """Proporciona el caso de uso GetReferenceFeatures"""
    return GetReferenceFeaturesUseCase(exercise_repo, features_repo)


async def get_features_for_comparison_use_case(
    features_repo = Depends(get_reference_features_repository)
) -> GetReferenceFeaturesForComparisonUseCase:
    """Proporciona el caso de uso GetReferenceFeaturesForComparison"""
    return GetReferenceFeaturesForComparisonUseCase(features_repo)


# ========================================
# CONTROLLER DEPENDENCIES
# ========================================

async def get_exercise_controller(
    get_exercises_uc = Depends(get_exercises_use_case),
    get_by_id_uc = Depends(get_exercise_by_id_use_case),
    get_details_uc = Depends(get_exercise_details_use_case),
    get_features_uc = Depends(get_reference_features_use_case),
    get_features_comparison_uc = Depends(get_features_for_comparison_use_case)
) -> ExerciseController:
    """
    Proporciona una instancia del controlador de ejercicios.
    
    Returns:
        ExerciseController: Controlador configurado con todos los casos de uso
    """
    return ExerciseController(
        get_exercises_use_case=get_exercises_uc,
        get_exercise_by_id_use_case=get_by_id_uc,
        get_exercise_details_use_case=get_details_uc,
        get_reference_features_use_case=get_features_uc,
        get_features_for_comparison_use_case=get_features_comparison_uc
    )


async def get_health_controller(
    exercise_repo = Depends(get_exercise_repository),
    features_repo = Depends(get_reference_features_repository)
) -> ExerciseHealthController:
    """
    Proporciona una instancia del controlador de salud.
    
    Returns:
        ExerciseHealthController: Controlador de salud
    """
    return ExerciseHealthController(
        exercise_repository=exercise_repo,
        reference_features_repository=features_repo
    )


# ========================================
# UTILITY FUNCTIONS
# ========================================

async def initialize_repositories():
    """
    Inicializa los repositorios (crear índices, etc.).
    Llamar desde main.py al arrancar la aplicación.
    """
    if _mongo_client:
        # Crear índices en MongoDB
        features_repo = MongoReferenceFeaturesRepository(_mongo_client)
        await features_repo.create_indexes()


async def cleanup_connections():
    """
    Limpia las conexiones (llamar al cerrar la aplicación).
    """
    global _postgres_pool, _mongo_client
    
    if _postgres_pool:
        await _postgres_pool.close()
        _postgres_pool = None
    
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None

