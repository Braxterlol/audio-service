"""
Infrastructure Layer - Audio Processing

Capa de infraestructura con repositorios, controladores y rutas.
"""

# Importar solo lo necesario para el main.py
# NO usar import * para evitar imports circulares

# Importar funciones de configuración directamente desde dependencies
# (sin pasar por helpers/__init__.py)
from src.audio_processing.infrastructure.helpers.dependencies import (
    audio_set_postgres_pool,
    audio_set_mongo_client,
    audio_initialize_repositories
)

# Importar routers
from src.audio_processing.infrastructure.routes.audio_processing_routes import  audio_processing_router
from src.audio_processing.infrastructure.routes.attempt_routes import  attempt_router

__all__ = [
    # Funciones de configuración
    'audio_set_postgres_pool',
    'audio_set_mongo_client',
    'audio_initialize_repositories',
    
    # Routers
    'audio_processing_router',
    'attempt_router'
]