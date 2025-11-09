"""
GetUserAttemptsUseCase - Obtener historial de intentos del usuario.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta
from src.audio_processing.domain.models.attempt import Attempt, AttemptStatus
from src.audio_processing.domain.repositories.attempt_repository import AttemptRepository


@dataclass
class GetUserAttemptsRequest:
    """DTO para la petición"""
    user_id: str
    exercise_id: Optional[str] = None  # Filtrar por ejercicio específico
    status: Optional[AttemptStatus] = None  # Filtrar por estado
    days: Optional[int] = None  # Últimos N días
    limit: int = 20
    offset: int = 0


@dataclass
class GetUserAttemptsResponse:
    """DTO para la respuesta"""
    attempts: List[Attempt]
    total: int
    limit: int
    offset: int
    has_more: bool
    
    def to_dict(self) -> dict:
        return {
            "attempts": [
                {
                    "id": attempt.id,
                    "exercise_id": attempt.exercise_id,
                    "attempted_at": attempt.attempted_at.isoformat(),
                    "status": attempt.status.value,
                    "quality": {
                        "score": round(attempt.audio_quality_score, 2) if attempt.audio_quality_score else None,
                        "snr_db": round(attempt.audio_snr_db, 2) if attempt.audio_snr_db else None,
                        "has_noise": attempt.has_background_noise,
                        "has_clipping": attempt.has_clipping
                    },
                    "metrics": {
                        "duration_seconds": round(attempt.total_duration_seconds, 2) if attempt.total_duration_seconds else None,
                        "speech_rate": round(attempt.speech_rate, 2) if attempt.speech_rate else None,
                        "articulation_rate": round(attempt.articulation_rate, 2) if attempt.articulation_rate else None,
                        "pause_count": attempt.pause_count
                    },
                    "scores": {
                        "overall": round(attempt.overall_score, 2) if attempt.overall_score else None,
                        "pronunciation": round(attempt.pronunciation_score, 2) if attempt.pronunciation_score else None,
                        "fluency": round(attempt.fluency_score, 2) if attempt.fluency_score else None,
                        "rhythm": round(attempt.rhythm_score, 2) if attempt.rhythm_score else None
                    },
                    "processing_time_ms": attempt.processing_time_ms,
                    "features_doc_id": attempt.features_doc_id
                }
                for attempt in self.attempts
            ],
            "pagination": {
                "total": self.total,
                "limit": self.limit,
                "offset": self.offset,
                "has_more": self.has_more,
                "returned": len(self.attempts)
            }
        }


class GetUserAttemptsUseCase:
    """
    Caso de uso: Obtener historial de intentos del usuario.
    
    Permite filtrar por ejercicio, estado, fecha y paginar resultados.
    """
    
    def __init__(self, attempt_repository: AttemptRepository):
        self.attempt_repository = attempt_repository
    
    async def execute(
        self,
        request: GetUserAttemptsRequest
    ) -> GetUserAttemptsResponse:
        """
        Ejecuta el caso de uso.
        
        Args:
            request: Parámetros de búsqueda
        
        Returns:
            GetUserAttemptsResponse: Lista de intentos
        """
        # Obtener intentos base
        if request.days:
            # Filtrar por fecha
            attempts = await self.attempt_repository.find_recent_by_user(
                user_id=request.user_id,
                days=request.days
            )
        else:
            # Obtener todos
            attempts = await self.attempt_repository.find_by_user_id(request.user_id)
        
        # Aplicar filtros adicionales
        filtered_attempts = self._apply_filters(attempts, request)
        
        # Ordenar por fecha (más reciente primero)
        filtered_attempts.sort(key=lambda a: a.attempted_at, reverse=True)
        
        # Calcular paginación
        total = len(filtered_attempts)
        start = request.offset
        end = request.offset + request.limit
        paginated = filtered_attempts[start:end]
        has_more = end < total
        
        return GetUserAttemptsResponse(
            attempts=paginated,
            total=total,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more
        )
    
    def _apply_filters(
        self,
        attempts: List[Attempt],
        request: GetUserAttemptsRequest
    ) -> List[Attempt]:
        """Aplica filtros opcionales."""
        result = attempts
        
        # Filtrar por exercise_id
        if request.exercise_id:
            result = [a for a in result if a.exercise_id == request.exercise_id]
        
        # Filtrar por status
        if request.status:
            result = [a for a in result if a.status == request.status]
        
        return result


@dataclass
class GetAttemptByIdRequest:
    """DTO para obtener un intento específico"""
    attempt_id: str
    user_id: str  # Para validar ownership


@dataclass
class GetAttemptByIdResponse:
    """DTO para la respuesta"""
    attempt: Attempt
    
    def to_dict(self) -> dict:
        attempt = self.attempt
        return {
            "id": attempt.id,
            "user_id": attempt.user_id,
            "exercise_id": attempt.exercise_id,
            "attempted_at": attempt.attempted_at.isoformat(),
            "status": attempt.status.value,
            "quality": {
                "score": round(attempt.audio_quality_score, 2) if attempt.audio_quality_score else None,
                "snr_db": round(attempt.audio_snr_db, 2) if attempt.audio_snr_db else None,
                "has_background_noise": attempt.has_background_noise,
                "has_clipping": attempt.has_clipping
            },
            "metrics": {
                "total_duration_seconds": round(attempt.total_duration_seconds, 2) if attempt.total_duration_seconds else None,
                "speech_rate": round(attempt.speech_rate, 2) if attempt.speech_rate else None,
                "articulation_rate": round(attempt.articulation_rate, 2) if attempt.articulation_rate else None,
                "pause_count": attempt.pause_count
            },
            "scores": {
                "overall_score": round(attempt.overall_score, 2) if attempt.overall_score else None,
                "pronunciation_score": round(attempt.pronunciation_score, 2) if attempt.pronunciation_score else None,
                "fluency_score": round(attempt.fluency_score, 2) if attempt.fluency_score else None,
                "rhythm_score": round(attempt.rhythm_score, 2) if attempt.rhythm_score else None
            },
            "analysis": {
                "error_count": attempt.error_count,
                "analyzed_at": attempt.analyzed_at.isoformat() if attempt.analyzed_at else None
            },
            "processing": {
                "processing_time_ms": attempt.processing_time_ms,
                "features_doc_id": attempt.features_doc_id
            },
            "timestamps": {
                "attempted_at": attempt.attempted_at.isoformat(),
                "analyzed_at": attempt.analyzed_at.isoformat() if attempt.analyzed_at else None
            }
        }


class GetAttemptByIdUseCase:
    """
    Caso de uso: Obtener detalle de un intento específico.
    
    Valida ownership del intento antes de retornarlo.
    """
    
    def __init__(self, attempt_repository: AttemptRepository):
        self.attempt_repository = attempt_repository
    
    async def execute(
        self,
        request: GetAttemptByIdRequest
    ) -> GetAttemptByIdResponse:
        """
        Ejecuta el caso de uso.
        
        Args:
            request: ID del intento y usuario
        
        Returns:
            GetAttemptByIdResponse: Detalle del intento
        
        Raises:
            ValueError: Si el intento no existe o no pertenece al usuario
        """
        # Buscar intento
        attempt = await self.attempt_repository.find_by_id(request.attempt_id)
        
        if not attempt:
            raise ValueError(f"Intento {request.attempt_id} no encontrado")
        
        # Validar ownership
        if attempt.user_id != request.user_id:
            raise ValueError("No tienes permiso para acceder a este intento")
        
        return GetAttemptByIdResponse(attempt=attempt)