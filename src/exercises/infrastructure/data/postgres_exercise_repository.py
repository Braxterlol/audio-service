"""
PostgreSQL implementation of ExerciseRepository.

Implementa el puerto ExerciseRepository usando PostgreSQL con asyncpg.
"""

from typing import List, Optional
from datetime import datetime
import asyncpg
from src.exercises.domain.models.exercise import (
    Exercise,
    ExerciseCategory,
    DifficultyLevel
)
from src.exercises.domain.repositories.exercise_repository import ExerciseRepository


class PostgresExerciseRepository(ExerciseRepository):
    """
    Implementación de ExerciseRepository usando PostgreSQL.
    
    Asume una tabla 'exercises' con el siguiente schema:
    - id: UUID PRIMARY KEY
    - exercise_id: VARCHAR UNIQUE NOT NULL
    - category: VARCHAR NOT NULL
    - subcategory: VARCHAR NOT NULL
    - text_content: TEXT NOT NULL
    - difficulty_level: INTEGER NOT NULL
    - target_phonemes: jsonb DEFAULT '[]'
    - reference_audio_s3_url: TEXT NOT NULL
    - is_active: BOOLEAN DEFAULT TRUE
    - created_at: TIMESTAMP DEFAULT NOW()
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Args:
            db_pool: Pool de conexiones de asyncpg
        """
        self.db_pool = db_pool
    
    async def find_by_id(self, exercise_id: str) -> Optional[Exercise]:
        """Busca ejercicio por UUID"""
        query = """
            SELECT id, exercise_id, category, subcategory, text_content,
                   difficulty_level, target_phonemes, reference_audio_s3_url,
                   is_active, created_at
            FROM exercises
            WHERE id = $1 AND is_active = TRUE
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, exercise_id)
            
            if not row:
                return None
            
            return self._map_row_to_exercise(row)
    
    async def find_by_exercise_id(self, exercise_id: str) -> Optional[Exercise]:
        """Busca ejercicio por exercise_id (ej: 'fonema_r_suave_1')"""
        query = """
            SELECT id, exercise_id, category, subcategory, text_content,
                   difficulty_level, target_phonemes, reference_audio_s3_url,
                   is_active, created_at
            FROM exercises
            WHERE exercise_id = $1 AND is_active = TRUE
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, exercise_id)
            
            if not row:
                return None
            
            return self._map_row_to_exercise(row)
    
    async def find_all(
        self,
        category: Optional[ExerciseCategory] = None,
        subcategory: Optional[str] = None,
        difficulty_level: Optional[int] = None,
        is_active: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[Exercise]:
        """Busca ejercicios con filtros"""
        # Construir query dinámicamente según filtros
        conditions = ["is_active = $1"]
        params = [is_active]
        param_count = 1
        
        if category:
            param_count += 1
            conditions.append(f"category = ${param_count}")
            params.append(category.value)
        
        if subcategory:
            param_count += 1
            conditions.append(f"subcategory = ${param_count}")
            params.append(subcategory)
        
        if difficulty_level:
            param_count += 1
            conditions.append(f"difficulty_level = ${param_count}")
            params.append(difficulty_level)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT id, exercise_id, category, subcategory, text_content,
                   difficulty_level, target_phonemes, reference_audio_s3_url,
                   is_active, created_at
            FROM exercises
            WHERE {where_clause}
            ORDER BY category, subcategory, difficulty_level
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        
        params.extend([limit, offset])
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            return [self._map_row_to_exercise(row) for row in rows]
    
    async def count(
        self,
        category: Optional[ExerciseCategory] = None,
        is_active: bool = True
    ) -> int:
        """Cuenta ejercicios"""
        conditions = ["is_active = $1"]
        params = [is_active]
        
        if category:
            conditions.append("category = $2")
            params.append(category.value)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT COUNT(*) as total
            FROM exercises
            WHERE {where_clause}
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            return row['total']
    
    async def save(self, exercise: Exercise) -> Exercise:
        """Guarda o actualiza un ejercicio"""
        # Intentar actualizar primero
        update_query = """
            UPDATE exercises
            SET category = $2,
                subcategory = $3,
                text_content = $4,
                difficulty_level = $5,
                target_phonemes = $6,
                reference_audio_s3_url = $7,
                is_active = $8
            WHERE id = $1
            RETURNING id
        """
        
        insert_query = """
            INSERT INTO exercises (
                id, exercise_id, category, subcategory, text_content,
                    difficulty_level, target_phonemes, reference_audio_s3_url,
                is_active, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """
        
        async with self.db_pool.acquire() as conn:
            # Intentar actualizar
            result = await conn.fetchrow(
                update_query,
                exercise.id,
                exercise.category.value,
                exercise.subcategory,
                exercise.text_content,
                exercise.difficulty_level.value,
                exercise.target_phonemes,
                exercise.reference_audio_url,
                exercise.is_active
            )
            
            # Si no existía, insertar
            if not result:
                await conn.fetchrow(
                    insert_query,
                    exercise.id,
                    exercise.exercise_id,
                    exercise.category.value,
                    exercise.subcategory,
                    exercise.text_content,
                    exercise.difficulty_level.value,
                    exercise.target_phonemes,
                    exercise.reference_audio_url,
                    exercise.is_active,
                    exercise.created_at
                )
            
            return exercise
    
    async def delete(self, exercise_id: str) -> bool:
        """Soft delete de un ejercicio"""
        query = """
            UPDATE exercises
            SET is_active = FALSE
            WHERE id = $1
            RETURNING id
        """
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(query, exercise_id)
            return result is not None
    
    async def exists(self, exercise_id: str) -> bool:
        """Verifica si existe un ejercicio"""
        query = """
            SELECT EXISTS(
                SELECT 1 FROM exercises
                WHERE exercise_id = $1 AND is_active = TRUE
            ) as exists
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, exercise_id)
            return row['exists']
    
    async def find_by_category_grouped(
        self,
        category: ExerciseCategory
    ) -> dict[str, List[Exercise]]:
        """Obtiene ejercicios agrupados por subcategoría"""
        query = """
            SELECT id, exercise_id, category, subcategory, text_content,
                   difficulty_level, target_phonemes, reference_audio_s3_url,
                   is_active, created_at
            FROM exercises
            WHERE category = $1 AND is_active = TRUE
            ORDER BY subcategory, difficulty_level
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, category.value)
            
            # Agrupar por subcategoría
            grouped = {}
            for row in rows:
                exercise = self._map_row_to_exercise(row)
                subcategory = exercise.subcategory
                
                if subcategory not in grouped:
                    grouped[subcategory] = []
                
                grouped[subcategory].append(exercise)
            
            return grouped
    
    def _map_row_to_exercise(self, row: asyncpg.Record) -> Exercise:
        """Convierte una fila de BD a entidad Exercise"""
        return Exercise(
            id=str(row['id']),
            exercise_id=row['exercise_id'],
            category=ExerciseCategory(row['category']),
            subcategory=row['subcategory'],
            text_content=row['text_content'],
            difficulty_level=DifficultyLevel(row['difficulty_level']),
            target_phonemes=list(row['target_phonemes']) if row['target_phonemes'] else [],
            reference_audio_url=row['reference_audio_s3_url'],
            is_active=row['is_active'],
            created_at=row['created_at']
        )

