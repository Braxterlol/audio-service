"""
Main Application - Audio Processing Service

Servicio de procesamiento de audio para ejercicios fonéticos.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.shared.config import settings

from src.exercise_progression.infrastructure.routes.exercise_routes import exercise_router

# Importar gestores de base de datos
from src.db import postgres_db, mongo_db

# Importar módulo de ejercicios
from src.exercises.infrastructure import (
    exercises_router,
    health_router as exercises_health_router,
    set_postgres_pool as exercises_set_postgres_pool,
    set_mongo_client as exercises_set_mongo_client,
    initialize_repositories as exercises_initialize_repositories
)

# Importar módulo de audio_processing
from src.audio_processing.infrastructure import (
    audio_processing_router,
    attempt_router,
    audio_set_postgres_pool as audio_set_postgres_pool,
    audio_set_mongo_client as audio_set_mongo_client,
    audio_initialize_repositories as audio_initialize_repositories
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación (startup y shutdown).
    """
    # ========================================
    # STARTUP
    # ========================================
    print("\n" + "="*50)
    print("🚀 Iniciando Audio Processing Service")
    print("="*50)
    
    try:
        # Conectar a PostgreSQL
        print("\n📦 Conectando a PostgreSQL...")
        await postgres_db.connect()
        
        # Conectar a MongoDB
        print("\n📦 Conectando a MongoDB...")
        mongo_db.connect()
        
        # Configurar módulo de ejercicios
        print("\n🔧 Configurando módulo de ejercicios...")
        exercises_set_postgres_pool(postgres_db.get_pool())
        exercises_set_mongo_client(mongo_db.get_client())
        
        # Inicializar repositorios de ejercicios
        print("  📊 Inicializando repositorios de ejercicios...")
        await exercises_initialize_repositories()
        
        # Configurar módulo de audio_processing
        print("\n🔧 Configurando módulo de audio_processing...")
        audio_set_postgres_pool(postgres_db.get_pool())
        audio_set_mongo_client(mongo_db.get_client())
        
        # Inicializar repositorios de audio_processing
        print("  📊 Inicializando repositorios de audio_processing...")
        await audio_initialize_repositories()
        
        print("\n" + "="*50)
        print("✨ Aplicación iniciada correctamente")
        print("="*50)
        print(f"\n📚 Documentación: http://localhost:{settings.PORT}/docs")
        print(f"🔍 Health check: http://localhost:{settings.PORT}/health")
        print(f"💪 Ejercicios: http://localhost:{settings.PORT}/api/v1/exercises")
        print(f"🎤 Audio Processing: http://localhost:{settings.PORT}/api/v1/audio")
        print(f"📊 Attempts: http://localhost:{settings.PORT}/api/v1/attempts\n")
        
    except Exception as e:
        print(f"\n❌ Error al iniciar la aplicación: {e}")
        raise
    
    yield
    
    # ========================================
    # SHUTDOWN
    # ========================================
    print("\n" + "="*50)
    print("👋 Cerrando Audio Processing Service")
    print("="*50)
    
    # Cerrar conexiones
    print("\n🔌 Cerrando conexiones...")
    await postgres_db.disconnect()
    mongo_db.disconnect()
    
    print("\n✅ Aplicación cerrada correctamente\n")


# ========================================
# CREAR APLICACIÓN
# ========================================

app = FastAPI(
    title=settings.SERVICE_NAME,
    description="API para gestión y procesamiento de ejercicios fonéticos",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ========================================
# MIDDLEWARE
# ========================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# ROUTES
# ========================================

# Endpoint raíz
@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "name": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "exercises": "/api/v1/exercises",
            "exercises_health": "/api/v1/exercises/health",
            "statistics": "/api/v1/exercises/statistics",
            "audio_processing": "/api/v1/audio",
            "attempts": "/api/v1/attempts",
            "progress": "/api/v1/attempts/progress/summary"
        }
    }


# Health check general
@app.get("/health")
async def health():
    """Health check general de la aplicación"""
    db_status = {
        "postgres": "connected" if postgres_db.pool else "disconnected",
        "mongodb": "connected" if mongo_db.client else "disconnected",
    }
    
    return {
        "status": "healthy",
        "service": "audio-processing-service",
        "version": settings.SERVICE_VERSION,
        "databases": db_status
    }


# ========================================
# INCLUIR ROUTERS - EXERCISES
# ========================================

app.include_router(
    exercises_router,
    prefix="/api/v1"
)

app.include_router(
    exercises_health_router,
    prefix="/api/v1"
)


# ========================================
# INCLUIR ROUTERS - AUDIO PROCESSING
# ========================================

app.include_router(
    audio_processing_router,
    prefix="/api/v1"
)

app.include_router(
    attempt_router,
    prefix="/api/v1"
)

app.include_router(exercise_router, prefix="/api/v1/progression")

# ========================================
# EJECUCIÓN
# ========================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
