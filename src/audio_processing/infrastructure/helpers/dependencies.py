"""
Dependencies - Inyección de dependencias para FastAPI (Audio Processing).

Proporciona funciones para resolver dependencias de controladores,
repositorios y casos de uso del módulo audio_processing.
"""

from typing import AsyncGenerator
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorClient
import asyncpg


# ========================================
# DATABASE CONNECTIONS
# ========================================
# Estos serán inyectados desde la app principal

_postgres_pool: asyncpg.Pool = None
_mongo_client: AsyncIOMotorClient = None


def audio_set_postgres_pool(pool: asyncpg.Pool):
    """
    Configura el pool de PostgreSQL (llamar desde main.py al iniciar).
    
    Args:
        pool: Pool de conexiones asyncpg
    """
    global _postgres_pool
    _postgres_pool = pool


def audio_set_mongo_client(client: AsyncIOMotorClient):
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

async def get_attempt_repository(
    db_pool: asyncpg.Pool = Depends(get_postgres_pool)
):
    """Proporciona una instancia del repositorio de intentos."""
    # Lazy import para evitar circular imports
    from src.audio_processing.infrastructure.data.attempt_repository_impl import (
        AttemptRepositoryImpl
    )
    return AttemptRepositoryImpl(db_pool)


async def get_audio_features_repository(
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client)
):
    """Proporciona una instancia del repositorio de audio features."""
    # Lazy import
    from src.audio_processing.infrastructure.data.audio_features_repository_impl import (
        AudioFeaturesRepositoryImpl
    )
    from src.shared.config import settings
    return AudioFeaturesRepositoryImpl(mongo_client, settings.MONGODB_DB)


async def get_phoneme_error_repository(
    db_pool: asyncpg.Pool = Depends(get_postgres_pool)
):
    """Proporciona una instancia del repositorio de errores fonéticos."""
    # Lazy import
    from src.audio_processing.infrastructure.data.phoneme_error_repository_impl import (
        PhonemeErrorRepositoryImpl
    )
    return PhonemeErrorRepositoryImpl(db_pool)


async def get_exercise_repository(
    db_pool: asyncpg.Pool = Depends(get_postgres_pool)
):
    """Proporciona una instancia del repositorio de ejercicios."""
    # Lazy import
    from src.exercises.infrastructure.data.postgres_exercise_repository import (
        PostgresExerciseRepository
    )
    return PostgresExerciseRepository(db_pool)


# ========================================
# SERVICE DEPENDENCIES
# ========================================

async def get_audio_processing_service(
    attempt_repo = Depends(get_attempt_repository),
    audio_features_repo = Depends(get_audio_features_repository)
):
    """Proporciona una instancia del servicio de procesamiento de audio."""
    # Lazy import
    from src.audio_processing.application.services.audio_processing_service import (
        AudioProcessingService
    )
    return AudioProcessingService(
        attempt_repository=attempt_repo,
        audio_features_repository=audio_features_repo
    )


async def get_validation_service(
    attempt_repo = Depends(get_attempt_repository),
    exercise_repo = Depends(get_exercise_repository)
):
    """Proporciona una instancia del servicio de validación."""
    # Lazy import
    from src.audio_processing.application.services.validation_service import (
        ValidationService
    )
    return ValidationService(
        attempt_repository=attempt_repo,
        exercise_repository=exercise_repo
    )


# ========================================
# USE CASE DEPENDENCIES
# ========================================

async def get_process_audio_use_case(
    audio_processing_service = Depends(get_audio_processing_service),
    validation_service = Depends(get_validation_service)
):
    """Proporciona el caso de uso ProcessAudio"""
    # Lazy import
    from src.audio_processing.application.use_cases.process_audio_use_case import (
        ProcessAudioUseCase
    )
    return ProcessAudioUseCase(
        audio_processing_service=audio_processing_service,
        validation_service=validation_service
    )


async def get_validate_audio_quality_use_case(
    audio_processing_service = Depends(get_audio_processing_service)
):
    """Proporciona el caso de uso ValidateAudioQuality"""
    # Lazy import
    from src.audio_processing.application.use_cases.validate_audio_quality_use_case import (
        ValidateAudioQualityUseCase
    )
    return ValidateAudioQualityUseCase(
        audio_processing_service=audio_processing_service
    )


async def get_user_attempts_use_case(
    attempt_repo = Depends(get_attempt_repository)
):
    """Proporciona el caso de uso GetUserAttempts"""
    # Lazy import
    from src.audio_processing.application.use_cases.get_attempts_use_case import (
        GetUserAttemptsUseCase
    )
    return GetUserAttemptsUseCase(
        attempt_repository=attempt_repo
    )


async def get_attempt_by_id_use_case(
    attempt_repo = Depends(get_attempt_repository)
):
    """Proporciona el caso de uso GetAttemptById"""
    # Lazy import
    from src.audio_processing.application.use_cases.get_attempts_use_case import (
        GetAttemptByIdUseCase
    )
    return GetAttemptByIdUseCase(
        attempt_repository=attempt_repo
    )


async def get_user_progress_use_case(
    attempt_repo = Depends(get_attempt_repository),
    exercise_repo = Depends(get_exercise_repository)
):
    """Proporciona el caso de uso GetUserProgress"""
    # Lazy import
    from src.audio_processing.application.use_cases.get_user_progress_use_case import (
        GetUserProgressUseCase
    )
    return GetUserProgressUseCase(
        attempt_repository=attempt_repo,
        exercise_repository=exercise_repo
    )


# ========================================
# CONTROLLER DEPENDENCIES
# ========================================

async def get_audio_processing_controller(
    process_audio_uc = Depends(get_process_audio_use_case),
    validate_audio_uc = Depends(get_validate_audio_quality_use_case)
):
    """Proporciona una instancia del controlador de procesamiento de audio."""
    # Lazy import
    from src.audio_processing.infrastructure.controllers.audio_processing_controller import (
        AudioProcessingController
    )
    return AudioProcessingController(
        process_audio_use_case=process_audio_uc,
        validate_audio_use_case=validate_audio_uc
    )


async def get_attempt_controller(
    get_attempts_uc = Depends(get_user_attempts_use_case),
    get_attempt_by_id_uc = Depends(get_attempt_by_id_use_case),
    get_progress_uc = Depends(get_user_progress_use_case)
):
    """Proporciona una instancia del controlador de intentos."""
    # Lazy import
    from src.audio_processing.infrastructure.controllers.attempt_controller import (
        AttemptController
    )
    return AttemptController(
        get_attempts_use_case=get_attempts_uc,
        get_attempt_by_id_use_case=get_attempt_by_id_uc,
        get_progress_use_case=get_progress_uc
    )


# ========================================
# UTILITY FUNCTIONS
# ========================================

async def audio_initialize_repositories():
    """
    Inicializa los repositorios (crear índices, etc.).
    Llamar desde main.py al arrancar la aplicación.
    """
    if _mongo_client:
        # Lazy import
        from src.audio_processing.infrastructure.data.audio_features_repository_impl import (
            AudioFeaturesRepositoryImpl
        )
        from src.shared.config import settings
        
        # Crear índices en MongoDB
        audio_features_repo = AudioFeaturesRepositoryImpl(_mongo_client, settings.MONGODB_DB)
        await audio_features_repo.create_indexes()
        print("  ✅ Índices de audio_features creados")


async def cleanup_connections():
    """Limpia las conexiones (llamar al cerrar la aplicación)."""
    global _postgres_pool, _mongo_client
    
    if _postgres_pool:
        await _postgres_pool.close()
        _postgres_pool = None
    
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None