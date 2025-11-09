"""
GetUserProgressUseCase - Obtener progreso y estadísticas del usuario.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from src.audio_processing.domain.models.attempt import Attempt, AttemptStatus
from src.audio_processing.domain.repositories.attempt_repository import AttemptRepository
from src.exercises.domain.repositories.exercise_repository import ExerciseRepository


@dataclass
class GetUserProgressRequest:
    """DTO para la petición"""
    user_id: str
    days: int = 30  # Período de análisis (últimos N días)


@dataclass
class GetUserProgressResponse:
    """DTO para la respuesta"""
    user_id: str
    period_days: int
    summary: Dict
    scores_evolution: Dict
    exercises_stats: Dict
    activity_by_day: List[Dict]
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "period": {
                "days": self.period_days,
                "from": (datetime.utcnow() - timedelta(days=self.period_days)).date().isoformat(),
                "to": datetime.utcnow().date().isoformat()
            },
            "summary": self.summary,
            "scores_evolution": self.scores_evolution,
            "exercises_stats": self.exercises_stats,
            "activity_by_day": self.activity_by_day
        }


class GetUserProgressUseCase:
    """
    Caso de uso: Obtener progreso y estadísticas del usuario.
    
    Calcula métricas agregadas para mostrar progreso en la UI.
    """
    
    def __init__(
        self,
        attempt_repository: AttemptRepository,
        exercise_repository: ExerciseRepository
    ):
        self.attempt_repository = attempt_repository
        self.exercise_repository = exercise_repository
    
    async def execute(
        self,
        request: GetUserProgressRequest
    ) -> GetUserProgressResponse:
        """
        Ejecuta el caso de uso.
        
        Args:
            request: Parámetros de consulta
        
        Returns:
            GetUserProgressResponse: Progreso del usuario
        """
        # Obtener intentos del período
        attempts = await self.attempt_repository.find_recent_by_user(
            user_id=request.user_id,
            days=request.days
        )
        
        # Calcular resumen general
        summary = self._calculate_summary(attempts)
        
        # Calcular evolución de scores
        scores_evolution = self._calculate_scores_evolution(attempts)
        
        # Calcular estadísticas por ejercicio
        exercises_stats = await self._calculate_exercises_stats(attempts)
        
        # Calcular actividad por día
        activity_by_day = self._calculate_activity_by_day(attempts, request.days)
        
        return GetUserProgressResponse(
            user_id=request.user_id,
            period_days=request.days,
            summary=summary,
            scores_evolution=scores_evolution,
            exercises_stats=exercises_stats,
            activity_by_day=activity_by_day
        )
    
    def _calculate_summary(self, attempts: List[Attempt]) -> Dict:
        """Calcula métricas generales."""
        if not attempts:
            return {
                "total_attempts": 0,
                "completed_attempts": 0,
                "rejected_attempts": 0,
                "unique_exercises": 0,
                "average_scores": {
                    "overall": None,
                    "pronunciation": None,
                    "fluency": None,
                    "rhythm": None
                },
                "total_practice_time_minutes": 0
            }
        
        completed = [a for a in attempts if a.status == AttemptStatus.COMPLETED]
        rejected = [a for a in attempts if a.status == AttemptStatus.QUALITY_REJECTED]
        
        # Calcular promedios de scores (solo completados con scores)
        scored_attempts = [a for a in completed if a.overall_score is not None]
        
        avg_overall = sum(a.overall_score for a in scored_attempts) / len(scored_attempts) if scored_attempts else None
        avg_pronunciation = sum(a.pronunciation_score for a in scored_attempts if a.pronunciation_score) / len([a for a in scored_attempts if a.pronunciation_score]) if scored_attempts else None
        avg_fluency = sum(a.fluency_score for a in scored_attempts if a.fluency_score) / len([a for a in scored_attempts if a.fluency_score]) if scored_attempts else None
        avg_rhythm = sum(a.rhythm_score for a in scored_attempts if a.rhythm_score) / len([a for a in scored_attempts if a.rhythm_score]) if scored_attempts else None
        
        # Calcular tiempo total de práctica
        total_duration = sum(a.total_duration_seconds for a in completed if a.total_duration_seconds)
        
        return {
            "total_attempts": len(attempts),
            "completed_attempts": len(completed),
            "rejected_attempts": len(rejected),
            "unique_exercises": len(set(a.exercise_id for a in attempts)),
            "average_scores": {
                "overall": round(avg_overall, 2) if avg_overall else None,
                "pronunciation": round(avg_pronunciation, 2) if avg_pronunciation else None,
                "fluency": round(avg_fluency, 2) if avg_fluency else None,
                "rhythm": round(avg_rhythm, 2) if avg_rhythm else None
            },
            "total_practice_time_minutes": round(total_duration / 60, 2) if total_duration else 0
        }
    
    def _calculate_scores_evolution(self, attempts: List[Attempt]) -> Dict:
        """Calcula la evolución de scores a lo largo del tiempo."""
        # Filtrar solo completados con scores
        scored = [a for a in attempts if a.status == AttemptStatus.COMPLETED and a.overall_score is not None]
        
        if not scored:
            return {
                "has_data": False,
                "trend": "no_data",
                "improvement": 0,
                "data_points": []
            }
        
        # Ordenar por fecha
        scored.sort(key=lambda a: a.attempted_at)
        
        # Crear puntos de datos
        data_points = [
            {
                "date": a.attempted_at.date().isoformat(),
                "overall_score": round(a.overall_score, 2),
                "pronunciation_score": round(a.pronunciation_score, 2) if a.pronunciation_score else None,
                "fluency_score": round(a.fluency_score, 2) if a.fluency_score else None,
                "rhythm_score": round(a.rhythm_score, 2) if a.rhythm_score else None
            }
            for a in scored
        ]
        
        # Calcular tendencia (comparar primeros vs últimos intentos)
        first_third = scored[:len(scored)//3] if len(scored) >= 3 else scored[:1]
        last_third = scored[-len(scored)//3:] if len(scored) >= 3 else scored[-1:]
        
        avg_first = sum(a.overall_score for a in first_third) / len(first_third)
        avg_last = sum(a.overall_score for a in last_third) / len(last_third)
        improvement = avg_last - avg_first
        
        trend = "improving" if improvement > 0.5 else "stable" if abs(improvement) <= 0.5 else "declining"
        
        return {
            "has_data": True,
            "trend": trend,
            "improvement": round(improvement, 2),
            "data_points": data_points
        }
    
    async def _calculate_exercises_stats(self, attempts: List[Attempt]) -> Dict:
        """Calcula estadísticas por ejercicio."""
        if not attempts:
            return {
                "by_exercise": [],
                "by_category": {}
            }
        
        # Agrupar por exercise_id
        by_exercise = defaultdict(list)
        for attempt in attempts:
            by_exercise[attempt.exercise_id].append(attempt)
        
        # Calcular stats por ejercicio
        exercise_stats = []
        for exercise_id, ex_attempts in by_exercise.items():
            completed = [a for a in ex_attempts if a.status == AttemptStatus.COMPLETED]
            scored = [a for a in completed if a.overall_score is not None]
            
            # Obtener info del ejercicio
            exercise = await self.exercise_repository.find_by_exercise_id(exercise_id)
            
            stats = {
                "exercise_id": exercise_id,
                "text_content": exercise.text_content if exercise else None,
                "category": exercise.category.value if exercise else "unknown",
                "total_attempts": len(ex_attempts),
                "completed_attempts": len(completed),
                "average_score": round(sum(a.overall_score for a in scored) / len(scored), 2) if scored else None,
                "best_score": round(max(a.overall_score for a in scored), 2) if scored else None,
                "last_attempted": max(a.attempted_at for a in ex_attempts).isoformat()
            }
            exercise_stats.append(stats)
        
        # Ordenar por última práctica
        exercise_stats.sort(key=lambda x: x["last_attempted"], reverse=True)
        
        # Agrupar por categoría
        by_category = defaultdict(lambda: {"count": 0, "avg_score": []})
        for stat in exercise_stats:
            category = stat["category"]
            by_category[category]["count"] += stat["total_attempts"]
            if stat["average_score"]:
                by_category[category]["avg_score"].append(stat["average_score"])
        
        # Calcular promedios por categoría
        category_summary = {
            cat: {
                "total_attempts": data["count"],
                "average_score": round(sum(data["avg_score"]) / len(data["avg_score"]), 2) if data["avg_score"] else None
            }
            for cat, data in by_category.items()
        }
        
        return {
            "by_exercise": exercise_stats,
            "by_category": category_summary
        }
    
    def _calculate_activity_by_day(self, attempts: List[Attempt], days: int) -> List[Dict]:
        """Calcula la actividad diaria."""
        # Crear diccionario para todos los días del período
        today = datetime.utcnow().date()
        activity = {}
        
        for i in range(days):
            date = today - timedelta(days=i)
            activity[date] = {
                "date": date.isoformat(),
                "attempts": 0,
                "completed": 0,
                "practice_time_minutes": 0
            }
        
        # Agregar intentos a cada día
        for attempt in attempts:
            date = attempt.attempted_at.date()
            if date in activity:
                activity[date]["attempts"] += 1
                if attempt.status == AttemptStatus.COMPLETED:
                    activity[date]["completed"] += 1
                    if attempt.total_duration_seconds:
                        activity[date]["practice_time_minutes"] += attempt.total_duration_seconds / 60
        
        # Convertir a lista y ordenar cronológicamente
        result = list(activity.values())
        result.sort(key=lambda x: x["date"])
        
        # Redondear minutos
        for day in result:
            day["practice_time_minutes"] = round(day["practice_time_minutes"], 2)
        
        return result