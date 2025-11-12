"""
PostgreSQL implementation of AttemptRepository.

Implementa el puerto AttemptRepository usando PostgreSQL con asyncpg.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncpg
import numpy as np
from src.audio_processing.domain.models.attempt import Attempt, AttemptStatus
from src.audio_processing.domain.repositories.attempt_repository import AttemptRepository


class AttemptRepositoryImpl(AttemptRepository):
    """
    Implementación de AttemptRepository usando PostgreSQL con asyncpg.
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        """
        Args:
            db_pool: Pool de conexiones de asyncpg
        """
        self.db_pool = db_pool
    
    @staticmethod
    def _convert_to_python_type(value):
        """
        Convierte tipos de numpy a tipos nativos de Python.
        
        asyncpg no puede serializar numpy.bool_, numpy.float64, etc.
        """
        if value is None:
            return None
        
        # Convertir numpy bool a Python bool
        if isinstance(value, (np.bool_, bool)):
            return bool(value)
        
        # Convertir numpy float a Python float
        if isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value)
        
        # Convertir numpy int a Python int
        if isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        
        # Si ya es un tipo nativo de Python, retornarlo tal cual
        return value
    
    async def save(self, attempt: Attempt) -> Attempt:
        """
        Guarda o actualiza un intento.
        
        IMPORTANTE: 
        - Convierte numpy types a Python types
        - Si attempt.id es None, hace INSERT y Postgres genera el ID
        - Si attempt.id existe, hace UPDATE
        - Retorna el Attempt con el ID generado/actualizado
        """
        # Convertir todos los valores a tipos nativos de Python
        audio_quality_score = self._convert_to_python_type(attempt.audio_quality_score)
        audio_snr_db = self._convert_to_python_type(attempt.audio_snr_db)
        has_background_noise = self._convert_to_python_type(attempt.has_background_noise)
        has_clipping = self._convert_to_python_type(attempt.has_clipping)
        total_duration_seconds = self._convert_to_python_type(attempt.total_duration_seconds)
        speech_rate = self._convert_to_python_type(attempt.speech_rate)
        articulation_rate = self._convert_to_python_type(attempt.articulation_rate)
        pause_count = self._convert_to_python_type(attempt.pause_count)
        overall_score = self._convert_to_python_type(attempt.overall_score)
        pronunciation_score = self._convert_to_python_type(attempt.pronunciation_score)
        fluency_score = self._convert_to_python_type(attempt.fluency_score)
        rhythm_score = self._convert_to_python_type(attempt.rhythm_score)
        error_count = self._convert_to_python_type(attempt.error_count)
        processing_time_ms = self._convert_to_python_type(attempt.processing_time_ms)
        
        async with self.db_pool.acquire() as conn:
            # Si tiene ID, intentar UPDATE
            if attempt.id is not None:
                update_query = """
                    UPDATE attempts
                    SET status = $2,
                        audio_quality_score = $3,
                        audio_snr_db = $4,
                        has_background_noise = $5,
                        has_clipping = $6,
                        total_duration_seconds = $7,
                        speech_rate = $8,
                        articulation_rate = $9,
                        pause_count = $10,
                        overall_score = $11,
                        pronunciation_score = $12,
                        fluency_score = $13,
                        rhythm_score = $14,
                        error_count = $15,
                        features_doc_id = $16,
                        processing_time_ms = $17,
                        analyzed_at = $18
                    WHERE id = $1
                    RETURNING id
                """
                
                result = await conn.fetchrow(
                    update_query,
                    attempt.id,
                    attempt.status.value,
                    audio_quality_score,
                    audio_snr_db,
                    has_background_noise,
                    has_clipping,
                    total_duration_seconds,
                    speech_rate,
                    articulation_rate,
                    pause_count,
                    overall_score,
                    pronunciation_score,
                    fluency_score,
                    rhythm_score,
                    error_count,
                    attempt.features_doc_id,
                    processing_time_ms,
                    attempt.analyzed_at
                )
                
                if result:
                    return attempt
            
            # Si no tiene ID o el UPDATE falló, hacer INSERT
            insert_query = """
                INSERT INTO attempts (
                    user_id, exercise_id, attempted_at, status,
                    audio_quality_score, audio_snr_db, has_background_noise, has_clipping,
                    total_duration_seconds, speech_rate, articulation_rate, pause_count,
                    overall_score, pronunciation_score, fluency_score, rhythm_score,
                    error_count, features_doc_id, processing_time_ms, analyzed_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                RETURNING id
            """
            
            result = await conn.fetchrow(
                insert_query,
                attempt.user_id,
                attempt.exercise_id,
                attempt.attempted_at,
                attempt.status.value,
                audio_quality_score,
                audio_snr_db,
                has_background_noise,
                has_clipping,
                total_duration_seconds,
                speech_rate,
                articulation_rate,
                pause_count,
                overall_score,
                pronunciation_score,
                fluency_score,
                rhythm_score,
                error_count,
                attempt.features_doc_id,
                processing_time_ms,
                attempt.analyzed_at
            )
            
            # Asignar el ID generado por Postgres
            attempt.id = str(result['id'])
            
            return attempt
    
    async def find_by_id(self, attempt_id: str) -> Optional[Attempt]:
        """Busca un intento por ID"""
        query = """
            SELECT * FROM attempts WHERE id = $1
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, attempt_id)
            
            if not row:
                return None
            
            return self._map_row_to_attempt(row)
    
    async def find_by_user(
        self,
        user_id: str,
        exercise_id: Optional[str] = None,
        status: Optional[AttemptStatus] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Attempt]:
        """Busca intentos de un usuario con filtros"""
        conditions = ["user_id = $1"]
        params = [user_id]
        param_count = 1
        
        if exercise_id:
            param_count += 1
            conditions.append(f"exercise_id = ${param_count}")
            params.append(exercise_id)
        
        if status:
            param_count += 1
            conditions.append(f"status = ${param_count}")
            params.append(status.value)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT * FROM attempts
            WHERE {where_clause}
            ORDER BY attempted_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        
        params.extend([limit, offset])
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            
            return [self._map_row_to_attempt(row) for row in rows]
    
    async def find_by_user_id(self, user_id: str) -> List[Attempt]:
        """Busca todos los intentos de un usuario"""
        return await self.find_by_user(user_id, limit=1000)
    
    async def find_by_exercise(self, exercise_id: str, limit: int = 100) -> List[Attempt]:
        """Busca todos los intentos de un ejercicio"""
        query = """
            SELECT * FROM attempts
            WHERE exercise_id = $1
            ORDER BY attempted_at DESC
            LIMIT $2
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, exercise_id, limit)
            
            return [self._map_row_to_attempt(row) for row in rows]
    
    async def find_by_exercise_id(self, exercise_id: str) -> List[Attempt]:
        """Alias de find_by_exercise"""
        return await self.find_by_exercise(exercise_id)
    
    async def find_recent_by_user(self, user_id: str, days: int = 30) -> List[Attempt]:
        """Busca intentos recientes de un usuario"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = """
            SELECT * FROM attempts
            WHERE user_id = $1 AND attempted_at >= $2
            ORDER BY attempted_at DESC
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, cutoff_date)
            
            return [self._map_row_to_attempt(row) for row in rows]
    
    async def find_pending_analysis(self, limit: int = 100) -> List[Attempt]:
        """Busca intentos pendientes de análisis ML"""
        query = """
            SELECT * FROM attempts
            WHERE status = $1
            ORDER BY attempted_at ASC
            LIMIT $2
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, AttemptStatus.PENDING_ANALYSIS.value, limit)
            
            return [self._map_row_to_attempt(row) for row in rows]
    
    async def count_by_user(
        self,
        user_id: str,
        status: Optional[AttemptStatus] = None
    ) -> int:
        """Cuenta los intentos de un usuario"""
        if status:
            query = """
                SELECT COUNT(*) as total
                FROM attempts
                WHERE user_id = $1 AND status = $2
            """
            params = [user_id, status.value]
        else:
            query = """
                SELECT COUNT(*) as total
                FROM attempts
                WHERE user_id = $1
            """
            params = [user_id]
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, *params)
            return row['total']
    
    async def count_by_user_today(self, user_id: str) -> int:
        """Cuenta intentos del usuario en el día actual"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = """
            SELECT COUNT(*) as total
            FROM attempts
            WHERE user_id = $1 AND attempted_at >= $2
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, today_start)
            return row['total']
    
    async def update_scores(
        self,
        attempt_id: str,
        overall_score: float,
        pronunciation_score: float,
        fluency_score: float,
        rhythm_score: float
    ) -> bool:
        """Actualiza los scores de un intento (cuando ML Analysis los calcula)"""
        query = """
            UPDATE attempts
            SET overall_score = $2,
                pronunciation_score = $3,
                fluency_score = $4,
                rhythm_score = $5,
                analyzed_at = $6,
                status = $7
            WHERE id = $1
            RETURNING id
        """
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(
                query,
                attempt_id,
                overall_score,
                pronunciation_score,
                fluency_score,
                rhythm_score,
                datetime.utcnow(),
                AttemptStatus.COMPLETED.value
            )
            return result is not None
    
    async def get_user_statistics(self, user_id: str) -> Dict:
        """Obtiene estadísticas agregadas del usuario"""
        query = """
            SELECT 
                COUNT(*) as total_attempts,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_attempts,
                COUNT(CASE WHEN status = 'quality_rejected' THEN 1 END) as rejected_attempts,
                AVG(CASE WHEN overall_score IS NOT NULL THEN overall_score END) as avg_overall_score,
                AVG(CASE WHEN pronunciation_score IS NOT NULL THEN pronunciation_score END) as avg_pronunciation,
                AVG(CASE WHEN fluency_score IS NOT NULL THEN fluency_score END) as avg_fluency,
                AVG(CASE WHEN rhythm_score IS NOT NULL THEN rhythm_score END) as avg_rhythm,
                SUM(total_duration_seconds) as total_practice_time
            FROM attempts
            WHERE user_id = $1
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            
            return {
                "total_attempts": row['total_attempts'] or 0,
                "completed_attempts": row['completed_attempts'] or 0,
                "rejected_attempts": row['rejected_attempts'] or 0,
                "avg_overall_score": float(row['avg_overall_score']) if row['avg_overall_score'] else None,
                "avg_pronunciation": float(row['avg_pronunciation']) if row['avg_pronunciation'] else None,
                "avg_fluency": float(row['avg_fluency']) if row['avg_fluency'] else None,
                "avg_rhythm": float(row['avg_rhythm']) if row['avg_rhythm'] else None,
                "total_practice_time_seconds": float(row['total_practice_time']) if row['total_practice_time'] else 0
            }
    
    async def find_anomalies_by_user(
        self,
        user_id: str,
        threshold: float = 2.0
    ) -> List[Attempt]:
        """
        Encuentra intentos anómalos (scores muy bajos o muy altos comparados con el promedio del usuario).
        Útil para detectar intentos sospechosos o excepcionales.
        """
        # Primero calcular el promedio y desviación estándar del usuario
        stats_query = """
            SELECT 
                AVG(overall_score) as avg_score,
                STDDEV(overall_score) as std_score
            FROM attempts
            WHERE user_id = $1 AND overall_score IS NOT NULL
        """
        
        async with self.db_pool.acquire() as conn:
            stats = await conn.fetchrow(stats_query, user_id)
            
            if not stats['avg_score']:
                return []  # No hay datos suficientes
            
            avg = float(stats['avg_score'])
            std = float(stats['std_score']) if stats['std_score'] else 0
            
            if std == 0:
                return []  # No hay variación
            
            # Buscar intentos fuera de threshold * std
            lower_bound = avg - (threshold * std)
            upper_bound = avg + (threshold * std)
            
            anomaly_query = """
                SELECT * FROM attempts
                WHERE user_id = $1 
                AND overall_score IS NOT NULL
                AND (overall_score < $2 OR overall_score > $3)
                ORDER BY attempted_at DESC
                LIMIT 20
            """
            
            rows = await conn.fetch(anomaly_query, user_id, lower_bound, upper_bound)
            
            return [self._map_row_to_attempt(row) for row in rows]
    
    async def delete(self, attempt_id: str) -> bool:
        """Elimina un intento"""
        query = """
            DELETE FROM attempts WHERE id = $1 RETURNING id
        """
        
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(query, attempt_id)
            return result is not None
    
    def _map_row_to_attempt(self, row: asyncpg.Record) -> Attempt:
        """Convierte una fila de BD a entidad Attempt"""
        return Attempt(
            id=str(row['id']),
            user_id=str(row['user_id']),
            exercise_id=row['exercise_id'],
            attempted_at=row['attempted_at'],
            status=AttemptStatus(row['status']),
            audio_quality_score=row['audio_quality_score'],
            audio_snr_db=row['audio_snr_db'],
            has_background_noise=row['has_background_noise'],
            has_clipping=row['has_clipping'],
            total_duration_seconds=row['total_duration_seconds'],
            speech_rate=row['speech_rate'],
            articulation_rate=row['articulation_rate'],
            pause_count=row['pause_count'],
            overall_score=row['overall_score'],
            pronunciation_score=row['pronunciation_score'],
            fluency_score=row['fluency_score'],
            rhythm_score=row['rhythm_score'],
            error_count=row['error_count'],
            features_doc_id=str(row['features_doc_id']) if row['features_doc_id'] else None,
            processing_time_ms=row['processing_time_ms'],
            analyzed_at=row['analyzed_at']
        )