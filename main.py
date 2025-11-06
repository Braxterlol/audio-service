"""
Main Application - Audio Processing Service

Servicio de procesamiento de audio para ejercicios fonéticos.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.shared.config import settings

# Importar gestores de base de datos
from src.db import postgres_db, mongo_db

# Importar módulo de ejercicios
from src.exercises.infrastructure import (
    exercises_router,
    health_router,
    set_postgres_pool,
    set_mongo_client,
    initialize_repositories
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
        set_postgres_pool(postgres_db.get_pool())
        set_mongo_client(mongo_db.get_client())
        
        # Inicializar repositorios (crear índices)
        print("\n🔧 Inicializando repositorios...")
        await initialize_repositories()
        
        print("\n" + "="*50)
        print("✨ Aplicación iniciada correctamente")
        print("="*50)
        print(f"\n📚 Documentación: http://localhost:8000/docs")
        print(f"🔍 Health check: http://localhost:8000/health")
        print(f"💪 Ejercicios: http://localhost:8000/api/v1/exercises\n")
        
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
            "statistics": "/api/v1/exercises/statistics"
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


# Incluir routers del módulo de ejercicios
app.include_router(
    exercises_router,
    prefix="/api/v1"
)

app.include_router(
    health_router,
    prefix="/api/v1"
)


# ========================================
# EJECUCIÓN
# ========================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )

