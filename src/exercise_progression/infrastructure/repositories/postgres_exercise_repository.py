# src/exercise_progression/infrastructure/repositories/postgres_exercise_repository.py

import asyncpg
from typing import List, Optional
import uuid
import json
from src.exercise_progression.domain.repositories.exercise_repository import ExerciseRepository
from src.exercise_progression.domain.models.exercise import Exercise


class PostgresExerciseRepository(ExerciseRepository):
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def get_all_ordered(self) -> List[Exercise]:
        """Retorna todos los ejercicios ordenados por order_index ASC"""
        query = """
            SELECT id, exercise_id, order_index, category, subcategory,
                   text_content, difficulty_level, target_phonemes,
                   reference_audio_s3_url, is_active, created_at
            FROM exercises
            WHERE is_active = true
            ORDER BY order_index ASC
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [self._row_to_exercise(row) for row in rows]
    
    async def get_by_id(self, exercise_id: uuid.UUID) -> Optional[Exercise]:
        """Busca por UUID"""
        query = """
            SELECT id, exercise_id, order_index, category, subcategory,
                   text_content, difficulty_level, target_phonemes,
                   reference_audio_s3_url, is_active, created_at
            FROM exercises
            WHERE id = $1 AND is_active = true
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, exercise_id)
            return self._row_to_exercise(row) if row else None
    
    async def get_by_exercise_id(self, exercise_id: str) -> Optional[Exercise]:
        """Busca por exercise_id string"""
        query = """
            SELECT id, exercise_id, order_index, category, subcategory,
                   text_content, difficulty_level, target_phonemes,
                   reference_audio_s3_url, is_active, created_at
            FROM exercises
            WHERE exercise_id = $1 AND is_active = true
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, exercise_id)
            return self._row_to_exercise(row) if row else None
    
    async def get_by_order_index(self, order_index: int) -> Optional[Exercise]:
        """Busca por posición en el camino"""
        query = """
            SELECT id, exercise_id, order_index, category, subcategory,
                   text_content, difficulty_level, target_phonemes,
                   reference_audio_s3_url, is_active, created_at
            FROM exercises
            WHERE order_index = $1 AND is_active = true
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, order_index)
            return self._row_to_exercise(row) if row else None
    
    async def get_first_exercise(self) -> Optional[Exercise]:
        """Retorna el primer ejercicio (order_index = 1)"""
        return await self.get_by_order_index(1)
    
    async def get_by_category(self, category: str) -> List[Exercise]:
        """Retorna ejercicios de una categoría"""
        query = """
            SELECT id, exercise_id, order_index, category, subcategory,
                   text_content, difficulty_level, target_phonemes,
                   reference_audio_s3_url, is_active, created_at
            FROM exercises
            WHERE category = $1 AND is_active = true
            ORDER BY order_index ASC
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, category)
            return [self._row_to_exercise(row) for row in rows]
    
    async def count_total(self) -> int:
        """Cuenta total de ejercicios activos"""
        query = "SELECT COUNT(*) FROM exercises WHERE is_active = true"
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query)
    
    def _row_to_exercise(self, row: asyncpg.Record) -> Exercise:
        """Convierte una fila de DB a entidad Exercise"""
        return Exercise(
            id=row['id'],
            exercise_id=row['exercise_id'],
            order_index=row['order_index'],
            category=row['category'],
            subcategory=row['subcategory'],
            text_content=row['text_content'],
            difficulty_level=row['difficulty_level'],
            target_phonemes=row['target_phonemes'] if row['target_phonemes'] else [],
            reference_audio_s3_url=row['reference_audio_s3_url'],
            is_active=row['is_active'],
            created_at=row['created_at']
        )