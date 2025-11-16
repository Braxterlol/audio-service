# src/exercise_progression/infrastructure/repositories/postgres_user_exercise_progress_repository.py

import asyncpg
from typing import List, Optional
import uuid
from datetime import datetime
from src.exercise_progression.domain.repositories.user_exercise_progress_repository import UserExerciseProgressRepository
from src.exercise_progression.domain.models.user_exercise_progress import UserExerciseProgress


class PostgresUserExerciseProgressRepository(UserExerciseProgressRepository):
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def get_all_by_user(self, user_id: uuid.UUID) -> List[UserExerciseProgress]:
        """Retorna todo el progreso del usuario"""
        query = """
            SELECT id, user_id, exercise_id, status, best_score, attempts_count,
                   last_attempt_at, completed_at, created_at, updated_at
            FROM user_exercise_progress
            WHERE user_id = $1
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [self._row_to_progress(row) for row in rows]
    
    async def get_by_user_and_exercise(
        self, 
        user_id: uuid.UUID, 
        exercise_id: uuid.UUID
    ) -> Optional[UserExerciseProgress]:
        """Retorna progreso de un ejercicio específico"""
        query = """
            SELECT id, user_id, exercise_id, status, best_score, attempts_count,
                   last_attempt_at, completed_at, created_at, updated_at
            FROM user_exercise_progress
            WHERE user_id = $1 AND exercise_id = $2
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, exercise_id)
            return self._row_to_progress(row) if row else None
    
    async def save(self, progress: UserExerciseProgress) -> UserExerciseProgress:
        """Crea o actualiza progreso (UPSERT)"""
        query = """
            INSERT INTO user_exercise_progress (
                id, user_id, exercise_id, status, best_score, attempts_count,
                last_attempt_at, completed_at, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (user_id, exercise_id) 
            DO UPDATE SET
                status = EXCLUDED.status,
                best_score = EXCLUDED.best_score,
                attempts_count = EXCLUDED.attempts_count,
                last_attempt_at = EXCLUDED.last_attempt_at,
                completed_at = EXCLUDED.completed_at,
                updated_at = EXCLUDED.updated_at
            RETURNING id, user_id, exercise_id, status, best_score, attempts_count,
                      last_attempt_at, completed_at, created_at, updated_at
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                progress.id,
                progress.user_id,
                progress.exercise_id,
                progress.status,
                progress.best_score,
                progress.attempts_count,
                progress.last_attempt_at,
                progress.completed_at,
                progress.created_at,
                progress.updated_at
            )
            return self._row_to_progress(row)
    
    async def initialize_user_progress(self, user_id: uuid.UUID) -> None:
        """
        Inicializa progreso para un usuario nuevo.
        Crea registros para TODOS los ejercicios:
        - Primer ejercicio (order_index=1): status = "available"
        - Resto: status = "locked"
        """
        query = """
            INSERT INTO user_exercise_progress (
                id, user_id, exercise_id, status, best_score, attempts_count,
                last_attempt_at, completed_at, created_at, updated_at
            )
            SELECT 
                gen_random_uuid(),
                $1,
                e.id,
                CASE WHEN e.order_index = 1 THEN 'available' ELSE 'locked' END,
                NULL,
                0,
                NULL,
                NULL,
                NOW(),
                NOW()
            FROM exercises e
            WHERE e.is_active = true
            ON CONFLICT (user_id, exercise_id) DO NOTHING
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, user_id)
    
    async def get_completed_count(self, user_id: uuid.UUID) -> int:
        """Cuenta ejercicios completados (status = 'completed' o 'mastered')"""
        query = """
            SELECT COUNT(*) 
            FROM user_exercise_progress
            WHERE user_id = $1 
              AND status IN ('completed', 'mastered')
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, user_id)
    
    async def get_total_stars(self, user_id: uuid.UUID) -> int:
        """
        Suma total de estrellas.
        Calcula dinámicamente desde best_score:
        - 70-79: 1 estrella
        - 80-89: 2 estrellas
        - 90+: 3 estrellas
        """
        query = """
            SELECT SUM(
                CASE 
                    WHEN best_score >= 90 THEN 3
                    WHEN best_score >= 80 THEN 2
                    WHEN best_score >= 70 THEN 1
                    ELSE 0
                END
            ) as total_stars
            FROM user_exercise_progress
            WHERE user_id = $1 AND best_score IS NOT NULL
        """
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(query, user_id)
            return result if result else 0
    
    async def unlock_exercise(
        self, 
        user_id: uuid.UUID, 
        exercise_id: uuid.UUID
    ) -> None:
        """Cambia status de 'locked' a 'available'"""
        query = """
            UPDATE user_exercise_progress
            SET status = 'available',
                updated_at = NOW()
            WHERE user_id = $1 
              AND exercise_id = $2
              AND status = 'locked'
        """
        async with self.pool.acquire() as conn:
            await conn.execute(query, user_id, exercise_id)
    
    def _row_to_progress(self, row: asyncpg.Record) -> UserExerciseProgress:
    
        return UserExerciseProgress(
            id=row['id'],
            user_id=row['user_id'],
            exercise_id=uuid.UUID(row['exercise_id']) if isinstance(row['exercise_id'], str) else row['exercise_id'],  # ✅ Convertir a UUID
            status=row['status'],
            best_score=row['best_score'],
            attempts_count=row['attempts_count'],
            last_attempt_at=row['last_attempt_at'],
            completed_at=row['completed_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )