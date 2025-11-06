"""
Ejemplo de integración del módulo de ejercicios con FastAPI.

Este archivo muestra cómo integrar el módulo de ejercicios completo
en una aplicación FastAPI.
"""

from fastapi import FastAPI
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient

# Importar routers y helpers del módulo de ejercicios
from src.exercises.infrastructure import (
    exercises_router,
    health_router,
    set_postgres_pool,
    set_mongo_client,
    initialize_repositories,
    cleanup_connections
)

# Crear aplicación FastAPI
app = FastAPI(
    title="Audio Processing Service - Exercises Module",
    description="API para gestionar ejercicios fonéticos",
    version="1.0.0"
)


# ========================================
# CONFIGURACIÓN DE BASES DE DATOS
# ========================================

@app.on_event("startup")
async def startup_event():
    """
    Inicializa las conexiones a bases de datos al arrancar la aplicación.
    """
    print("🚀 Iniciando aplicación...")
    
    # Configurar PostgreSQL
    print("📦 Conectando a PostgreSQL...")
    postgres_pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        database="audio_processing",
        user="postgres",
        password="postgres",
        min_size=5,
        max_size=20
    )
    set_postgres_pool(postgres_pool)
    print("✅ PostgreSQL conectado")
    
    # Configurar MongoDB
    print("📦 Conectando a MongoDB...")
    mongo_client = AsyncIOMotorClient(
        "mongodb://localhost:27017",
        maxPoolSize=50,
        minPoolSize=10
    )
    set_mongo_client(mongo_client)
    print("✅ MongoDB conectado")
    
    # Inicializar repositorios (crear índices)
    print("🔧 Inicializando repositorios...")
    await initialize_repositories()
    print("✅ Repositorios inicializados")
    
    print("✨ Aplicación lista!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Limpia las conexiones al cerrar la aplicación.
    """
    print("👋 Cerrando aplicación...")
    await cleanup_connections()
    print("✅ Conexiones cerradas")


# ========================================
# REGISTRAR ROUTERS
# ========================================

# Router de ejercicios
app.include_router(
    exercises_router,
    prefix="/api/v1",
    tags=["exercises"]
)

# Router de health/monitoreo
app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["health"]
)


# ========================================
# ENDPOINTS ADICIONALES
# ========================================

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Audio Processing Service - Exercises Module",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "exercises": "/api/v1/exercises",
            "health": "/api/v1/exercises/health",
            "statistics": "/api/v1/exercises/statistics"
        }
    }


@app.get("/health")
async def health():
    """Health check general de la aplicación"""
    return {
        "status": "healthy",
        "service": "audio-processing-exercises"
    }


# ========================================
# CONFIGURACIÓN DE CORS (opcional)
# ========================================

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# EJECUCIÓN
# ========================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "INTEGRATION_EXAMPLE:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Solo en desarrollo
        log_level="info"
    )


# ========================================
# EJEMPLOS DE USO
# ========================================

"""
# Iniciar servidor:
python src/exercises/INTEGRATION_EXAMPLE.py

# O con uvicorn directamente:
uvicorn src.exercises.INTEGRATION_EXAMPLE:app --reload

# Documentación interactiva:
http://localhost:8000/docs

# EJEMPLOS DE REQUESTS:

# 1. Listar todos los ejercicios de fonemas
curl "http://localhost:8000/api/v1/exercises?category=fonema&limit=10"

# 2. Listar ejercicios de r_suave nivel 2
curl "http://localhost:8000/api/v1/exercises?category=fonema&subcategory=r_suave&difficulty_level=2"

# 3. Obtener ejercicio específico
curl "http://localhost:8000/api/v1/exercises/fonema_r_suave_1"

# 4. Obtener detalles completos (incluye relacionados)
curl "http://localhost:8000/api/v1/exercises/fonema_r_suave_1/details"

# 5. Obtener features de referencia completas
curl "http://localhost:8000/api/v1/exercises/fonema_r_suave_1/reference-features"

# 6. Obtener features optimizadas para comparación
curl "http://localhost:8000/api/v1/exercises/fonema_r_suave_1/features-comparison"

# 7. Health check del módulo
curl "http://localhost:8000/api/v1/exercises/health"

# 8. Estadísticas del módulo
curl "http://localhost:8000/api/v1/exercises/statistics"

# 9. Paginación
curl "http://localhost:8000/api/v1/exercises?limit=5&offset=10"

# 10. Filtrar activos/inactivos
curl "http://localhost:8000/api/v1/exercises?is_active=false"


# RESPUESTAS ESPERADAS:

# GET /api/v1/exercises
{
  "exercises": [
    {
      "id": "uuid-here",
      "exercise_id": "fonema_r_suave_1",
      "category": "fonema",
      "subcategory": "r_suave",
      "text_content": "raro",
      "difficulty_level": 2,
      "target_phonemes": ["/r/"],
      "reference_audio_url": "https://s3.../fonema_r_suave_1.wav",
      "instructions": "Pronuncia la palabra...",
      "tips": "Coloca la lengua...",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 45,
  "limit": 50,
  "offset": 0
}

# GET /api/v1/exercises/{id}
{
  "found": true,
  "exercise": {
    "id": "uuid-here",
    "exercise_id": "fonema_r_suave_1",
    ...
  }
}

# GET /api/v1/exercises/{id}/details
{
  "id": "uuid-here",
  "exercise_id": "fonema_r_suave_1",
  ...
  "related_exercises": [
    {
      "id": "uuid-2",
      "exercise_id": "fonema_r_suave_2",
      "text_content": "caro",
      "difficulty_level": 2
    }
  ],
  "expected_duration_range": [0.5, 2.0],
  "metadata": {
    "is_phoneme_exercise": true,
    "is_rhythm_exercise": false,
    "is_intonation_exercise": false,
    "has_target_phonemes": true
  }
}

# GET /api/v1/exercises/{id}/reference-features
{
  "found": true,
  "exercise_exists": true,
  "features": {
    "exercise_id": "fonema_r_suave_1",
    "mfcc_stats": {
      "mean": [13 valores],
      "std": [13 valores],
      "min": [13 valores],
      "max": [13 valores]
    },
    "prosody_stats": {
      "f0_mean": 120.5,
      "f0_std": 15.2,
      "f0_min": 90.0,
      "f0_max": 170.0,
      "f0_median": 118.0,
      "f0_range": 80.0,
      "jitter": 0.02,
      "shimmer": 0.03
    },
    "phoneme_segments": [
      {
        "phoneme": "/r/",
        "start_time": 0.1,
        "end_time": 0.3,
        "duration_ms": 200,
        "formant_f1": 500.0,
        "formant_f2": 1500.0,
        "formant_f3": 2500.0,
        "position_in_word": "inicial"
      }
    ],
    "duration_seconds": 1.5,
    "phoneme_count": 4,
    "normalization_params": {...},
    "thresholds": {...},
    "cache_version": "v1.0",
    "cached_at": "2024-01-01T00:00:00"
  }
}

# GET /api/v1/exercises/health
{
  "status": "healthy",
  "exercises_count": 45,
  "cached_features_count": 42,
  "cache_coverage": "93.3%"
}

# GET /api/v1/exercises/statistics
{
  "total_exercises": 45,
  "exercises_by_category": {
    "fonema": 20,
    "ritmo": 15,
    "entonacion": 10
  },
  "cached_features": 42,
  "cache_coverage_percentage": 93.33
}
"""

