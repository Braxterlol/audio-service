"""
PostgreSQL implementation of PhonemeErrorRepository.

Implementa el puerto PhonemeErrorRepository usando PostgreSQL con asyncpg.
"""

from typing import List, Optional, Dict
import asyncpg
from src.audio_processing.domain.models.phoneme_error import PhonemeError, ErrorType
from src.audio_processing.domain.repositories.phoneme_error_repository import PhonemeErrorRepository


class PhonemeErrorRepositoryImpl(PhonemeErrorRepository):
    """
    Implementación de PhonemeErrorRepository usando PostgreSQL con asyncpg.
    
    Asume una tabla 'phoneme_errors' con el siguiente schema:
    - id: UUID PRIMARY KEY
    - attempt_id: UUID NOT NULL
    - user_id: UUID NOT NULL
    - exercise_id: VARCHAR NOT NULL
    - expected_phoneme: VARCHAR NOT NULL
    - detected_phoneme: VARCHAR
    - error_type: VARCHAR NOT NULL
    - confidence: FLOAT NOT NULL
    - position: INTEGER NOT NULL
    - context: TEXT
    - detected_at: TIMESTAMP NOT NULL
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Args:
            db_pool: Pool de conexiones de asyncpg
        """
        self.db_pool = db_pool
    
    async def save(self, error: PhonemeError) -> PhonemeError:
        """Guarda un error fonético"""
        query = """
            INSERT INTO phoneme_errors (
                id, attempt_id, user_id, exercise_id,
                expected_phoneme, detected_phoneme, error_type,
                confidence, position, context, detected_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """
        
        async with self.db_pool.acquire() as conn:
            await conn.fetchrow(
                query,
                error.id,
                error.attempt_id,
                error.user_id,
                error.exercise_id,
                error.expected_phoneme,
                error.detected_phoneme,
                error.error_type.value,
                error.confidence,
                error.position,
                error.context,
                error.detected_at
            )
            
            return error
    
    async def save_batch(self, errors: List[PhonemeError]) -> List[PhonemeError]:
        """Guarda múltiples errores en batch"""
        query = """
            INSERT INTO phoneme_errors (
                id, attempt_id, user_id, exercise_id,
                expected_phoneme, detected_phoneme, error_type,
                confidence, position, context, detected_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        
        async with self.db_pool.acquire() as conn:
            # Preparar valores para batch insert
            values = [
                (
                    error.id,
                    error.attempt_id,
                    error.user_id,
                    error.exercise_id,
                    error.expected_phoneme,
                    error.detected_phoneme,
                    error.error_type.value,
                    error.confidence,
                    error.position,
                    error.context,
                    error.detected_at
                )
                for error in errors
            ]
            
            await conn.executemany(query, values)
            
            return errors
    
    async def find_by_attempt_id(self, attempt_id: str) -> List[PhonemeError]:
        """Busca errores de un intento"""
        query = """
            SELECT * FROM phoneme_errors
            WHERE attempt_id = $1
            ORDER BY position ASC
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, attempt_id)
            
            return [self._map_row_to_error(row) for row in rows]
    
    async def find_by_user_id(self, user_id: str, limit: int = 100) -> List[PhonemeError]:
        """Busca errores de un usuario"""
        query = """
            SELECT * FROM phoneme_errors
            WHERE user_id = $1
            ORDER BY detected_at DESC
            LIMIT $2
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, limit)
            
            return [self._map_row_to_error(row) for row in rows]
    
    async def find_by_phoneme(self, phoneme: str, limit: int = 100) -> List[PhonemeError]:
        """Busca errores de un fonema específico"""
        query = """
            SELECT * FROM phoneme_errors
            WHERE expected_phoneme = $1
            ORDER BY detected_at DESC
            LIMIT $2
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, phoneme, limit)
            
            return [self._map_row_to_error(row) for row in rows]
    
    async def get_error_stats_by_user(self, user_id: str) -> Dict:
        """Obtiene estadísticas de errores de un usuario"""
        errors = await self.find_by_user_id(user_id, limit=1000)
        
        if not errors:
            return {
                "total_errors": 0,
                "by_type": {},
                "by_phoneme": {},
                "most_common_errors": []
            }
        
        # Agrupar por tipo
        by_type = {}
        for error in errors:
            error_type = error.error_type.value
            by_type[error_type] = by_type.get(error_type, 0) + 1
        
        # Agrupar por fonema
        by_phoneme = {}
        for error in errors:
            phoneme = error.expected_phoneme
            by_phoneme[phoneme] = by_phoneme.get(phoneme, 0) + 1
        
        # Errores más comunes
        most_common = sorted(
            by_phoneme.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total_errors": len(errors),
            "by_type": by_type,
            "by_phoneme": by_phoneme,
            "most_common_errors": [
                {"phoneme": phoneme, "count": count}
                for phoneme, count in most_common
            ]
        }
    
    async def delete_by_attempt_id(self, attempt_id: str) -> int:
        """Elimina todos los errores de un intento"""
        query = """
            DELETE FROM phoneme_errors
            WHERE attempt_id = $1
            RETURNING id
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, attempt_id)
            return len(rows)
    
    def _map_row_to_error(self, row: asyncpg.Record) -> PhonemeError:
        """Convierte una fila de BD a entidad PhonemeError"""
        return PhonemeError(
            id=str(row['id']),
            attempt_id=str(row['attempt_id']),
            user_id=str(row['user_id']),
            exercise_id=row['exercise_id'],
            expected_phoneme=row['expected_phoneme'],
            detected_phoneme=row['detected_phoneme'],
            error_type=ErrorType(row['error_type']),
            confidence=row['confidence'],
            position=row['position'],
            context=row['context'],
            detected_at=row['detected_at']
        )