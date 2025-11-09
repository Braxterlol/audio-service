"""
UserProgressRepository - Implementación con PostgreSQL para gestionar progreso de usuarios.
"""

from typing import List, Optional
import asyncpg
from src.audio_processing.domain.models.user_exercise_progress_model import (
    UserExerciseProgress,
    ProgressStatus
)


class UserProgressRepository:
    """
    Repositorio para gestionar el progreso de usuarios en ejercicios.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Args:
            db_pool: Pool de conexiones de asyncpg
        """
        self.db_pool = db_pool
    
    async def find_by_user(self, user_id: str) -> List[UserExerciseProgress]:
        """Obtiene todo el progreso de un usuario."""
        query = """
            SELECT * FROM user_exercise_progress
            WHERE user_id = $1
            ORDER BY exercise_id
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [self._map_row_to_progress(row) for row in rows]
    
    async def find_by_user_and_exercise(
        self,
        user_id: str,
        exercise_id: str
    ) -> Optional[UserExerciseProgress]:
        """Obtiene el progreso de un usuario en un ejercicio específico."""
        query = """
            SELECT * FROM user_exercise_progress
            WHERE user_id = $1 AND exercise_id = $2
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, exercise_id)
            return self._map_row_to_progress(row) if row else None
    
    async def save(self, progress: UserExerciseProgress) -> UserExerciseProgress:
        """Guarda o actualiza el progreso."""
        query = """
            INSERT INTO user_exercise_progress (
                id, user_id, exercise_id, status, best_score, attempts_count,
                last_attempt_at, unlocked_at, completed_at, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
            ON CONFLICT (user_id, exercise_id)
            DO UPDATE SET
                status = $4,
                best_score = $5,
                attempts_count = $6,
                last_attempt_at = $7,
                unlocked_at = COALESCE($8, user_exercise_progress.unlocked_at),
                completed_at = COALESCE($9, user_exercise_progress.completed_at),
                updated_at = NOW()
            RETURNING *
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                progress.id,
                progress.user_id,
                progress.exercise_id,
                progress.status.value,
                progress.best_score,
                progress.attempts_count,
                progress.last_attempt_at,
                progress.unlocked_at,
                progress.completed_at
            )
            return self._map_row_to_progress(row)
    
    async def initialize_user_progress(self, user_id: str) -> List[str]:
        """
        Inicializa el progreso de un nuevo usuario.
        Desbloquea el primer ejercicio de cada categoría.
        
        Returns:
            List[str]: IDs de los ejercicios desbloqueados
        """
        query = """
            SELECT initialize_user_exercises($1)
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(query, user_id)
        
        # Obtener los ejercicios desbloqueados
        unlocked = await self.find_by_user_and_status(user_id, ProgressStatus.UNLOCKED)
        return [p.exercise_id for p in unlocked]
    
    async def unlock_next_exercise(
        self,
        user_id: str,
        completed_exercise_id: str
    ) -> Optional[str]:
        """
        Desbloquea el siguiente ejercicio después de completar uno.
        
        Returns:
            Optional[str]: ID del ejercicio desbloqueado o None si no hay más
        """
        query = """
            SELECT unlock_next_exercise($1, $2)
        """
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval(query, user_id, completed_exercise_id)
            return result
    
    async def find_by_user_and_status(
        self,
        user_id: str,
        status: ProgressStatus
    ) -> List[UserExerciseProgress]:
        """Obtiene ejercicios de un usuario con un estado específico."""
        query = """
            SELECT * FROM user_exercise_progress
            WHERE user_id = $1 AND status = $2
            ORDER BY exercise_id
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, status.value)
            return [self._map_row_to_progress(row) for row in rows]
    
    async def get_available_exercises(self, user_id: str) -> List[UserExerciseProgress]:
        """Obtiene todos los ejercicios disponibles (no bloqueados) para un usuario."""
        query = """
            SELECT * FROM user_exercise_progress
            WHERE user_id = $1 AND status != 'locked'
            ORDER BY exercise_id
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [self._map_row_to_progress(row) for row in rows]
    
    async def count_by_status(self, user_id: str, status: ProgressStatus) -> int:
        """Cuenta ejercicios de un usuario por estado."""
        query = """
            SELECT COUNT(*) as total
            FROM user_exercise_progress
            WHERE user_id = $1 AND status = $2
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, status.value)
            return row['total']
    
    def _map_row_to_progress(self, row: asyncpg.Record) -> UserExerciseProgress:
        """Convierte una fila de BD a UserExerciseProgress."""
        return UserExerciseProgress(
            id=str(row['id']),
            user_id=str(row['user_id']),
            exercise_id=row['exercise_id'],
            status=ProgressStatus(row['status']),
            best_score=row['best_score'],
            attempts_count=row['attempts_count'],
            last_attempt_at=row['last_attempt_at'],
            unlocked_at=row['unlocked_at'],
            completed_at=row['completed_at'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )