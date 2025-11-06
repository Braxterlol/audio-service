"""
Infrastructure Routes - FastAPI route definitions.
"""

from .exercise_routes import exercises_router, health_router

__all__ = [
    "exercises_router",
    "health_router"
]

