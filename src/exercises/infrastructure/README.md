# Infrastructure Layer - Exercises Module

Esta es la capa de infraestructura del módulo de ejercicios, implementando arquitectura hexagonal (puertos y adaptadores).

## 📁 Estructura

```
infrastructure/
├── __init__.py                 # Exporta componentes principales
├── controllers/                # Controladores HTTP
│   ├── __init__.py
│   └── exercise_controller.py  # Controladores de ejercicios
├── data/                       # Implementaciones de repositorios
│   ├── __init__.py
│   ├── postgres_exercise_repository.py      # Repositorio PostgreSQL
│   └── mongo_reference_features_repository.py  # Repositorio MongoDB
├── routes/                     # Definiciones de rutas FastAPI
│   ├── __init__.py
│   └── exercise_routes.py      # Rutas de ejercicios
└── helpers/                    # Utilidades
    ├── __init__.py
    ├── dependencies.py         # Inyección de dependencias
    ├── response_formatters.py  # Formateo de respuestas
    └── validators.py           # Validadores HTTP
```

## 🏗️ Componentes

### 1. Data Layer (Repositorios)

#### PostgresExerciseRepository
Implementación del repositorio de ejercicios usando PostgreSQL con asyncpg.

**Métodos:**
- `find_by_id(exercise_id)` - Buscar por UUID
- `find_by_exercise_id(exercise_id)` - Buscar por exercise_id
- `find_all(filters)` - Listar con filtros
- `count(filters)` - Contar ejercicios
- `save(exercise)` - Guardar/actualizar
- `delete(exercise_id)` - Soft delete
- `exists(exercise_id)` - Verificar existencia
- `find_by_category_grouped(category)` - Agrupar por subcategoría

**Schema de tabla:**
```sql
CREATE TABLE exercises (
    id UUID PRIMARY KEY,
    exercise_id VARCHAR UNIQUE NOT NULL,
    category VARCHAR NOT NULL,
    subcategory VARCHAR NOT NULL,
    text_content TEXT NOT NULL,
    difficulty_level INTEGER NOT NULL,
    target_phonemes TEXT[],
    reference_audio_url TEXT NOT NULL,
    instructions TEXT,
    tips TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### MongoReferenceFeaturesRepository
Implementación del repositorio de features de referencia usando MongoDB con motor.

**Métodos:**
- `find_by_exercise_id(exercise_id)` - Obtener features
- `save(features)` - Guardar features (upsert)
- `exists(exercise_id)` - Verificar existencia
- `delete(exercise_id)` - Eliminar features
- `find_all_cached()` - Listar todas
- `count_cached()` - Contar features
- `invalidate_cache(exercise_id)` - Invalidar caché
- `create_indexes()` - Crear índices necesarios

**Índices:**
- `exercise_id` (único)
- `cache_version`
- `cached_at`

### 2. Controllers

#### ExerciseController
Maneja las peticiones HTTP relacionadas con ejercicios.

**Responsabilidades:**
- Validar parámetros HTTP
- Invocar casos de uso apropiados
- Formatear respuestas HTTP
- Manejar errores y excepciones

**Métodos:**
- `get_exercises(filters)` - Lista paginada de ejercicios
- `get_exercise_by_id(id)` - Ejercicio específico
- `get_exercise_details(id)` - Detalles completos + relacionados
- `get_reference_features(id)` - Features completas de referencia
- `get_features_for_comparison(id)` - Features optimizadas para DTW

#### ExerciseHealthController
Maneja endpoints de salud y monitoreo.

**Métodos:**
- `health_check()` - Verifica estado del módulo
- `get_statistics()` - Estadísticas del módulo

### 3. Routes (FastAPI)

#### Endpoints disponibles:

**Ejercicios:**
- `GET /exercises` - Lista paginada con filtros
- `GET /exercises/{exercise_id}` - Ejercicio por ID
- `GET /exercises/{exercise_id}/details` - Detalles completos
- `GET /exercises/{exercise_id}/reference-features` - Features completas
- `GET /exercises/{exercise_id}/features-comparison` - Features para DTW

**Health:**
- `GET /exercises/health` - Estado de salud
- `GET /exercises/statistics` - Estadísticas del módulo

### 4. Helpers

#### Dependencies (dependencies.py)
Sistema de inyección de dependencias para FastAPI.

**Funciones principales:**
- `set_postgres_pool(pool)` - Configurar pool de PostgreSQL
- `set_mongo_client(client)` - Configurar cliente de MongoDB
- `initialize_repositories()` - Inicializar repositorios (crear índices)
- `cleanup_connections()` - Limpiar conexiones al cerrar

**Dependencies disponibles:**
- `get_exercise_repository()` - Repositorio de ejercicios
- `get_reference_features_repository()` - Repositorio de features
- `get_exercise_controller()` - Controlador de ejercicios
- `get_health_controller()` - Controlador de salud

#### Response Formatters (response_formatters.py)
Utilidades para formatear respuestas HTTP consistentes.

**Funciones:**
- `success_response(data, message)` - Respuesta exitosa
- `error_response(error, details)` - Respuesta de error
- `paginated_response(items, total, limit, offset)` - Respuesta paginada
- `not_found_response(resource, id)` - Recurso no encontrado
- `validation_error_response(field, message)` - Error de validación

#### Validators (validators.py)
Validadores para parámetros HTTP.

**Funciones:**
- `validate_exercise_id_format(id)` - Validar formato de exercise_id
- `validate_category(category)` - Validar categoría
- `validate_difficulty_level(level)` - Validar nivel de dificultad
- `validate_pagination_params(limit, offset)` - Validar paginación
- `validate_uuid_format(uuid_str)` - Validar formato UUID

## 🚀 Uso

### Configuración inicial (en main.py)

```python
from fastapi import FastAPI
from src.exercises.infrastructure import (
    exercises_router,
    health_router,
    set_postgres_pool,
    set_mongo_client,
    initialize_repositories,
    cleanup_connections
)
import asyncpg
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# Configurar conexiones
@app.on_event("startup")
async def startup():
    # PostgreSQL
    postgres_pool = await asyncpg.create_pool(
        host="localhost",
        database="audio_processing",
        user="user",
        password="password"
    )
    set_postgres_pool(postgres_pool)
    
    # MongoDB
    mongo_client = AsyncIOMotorClient("mongodb://localhost:27017")
    set_mongo_client(mongo_client)
    
    # Inicializar repositorios (crear índices)
    await initialize_repositories()

@app.on_event("shutdown")
async def shutdown():
    await cleanup_connections()

# Registrar routers
app.include_router(exercises_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
```

### Ejemplo de uso de endpoints

```bash
# Listar ejercicios
curl "http://localhost:8000/api/v1/exercises?category=fonema&limit=10"

# Obtener ejercicio específico
curl "http://localhost:8000/api/v1/exercises/fonema_r_suave_1"

# Obtener detalles completos
curl "http://localhost:8000/api/v1/exercises/fonema_r_suave_1/details"

# Obtener features de referencia
curl "http://localhost:8000/api/v1/exercises/fonema_r_suave_1/reference-features"

# Obtener features para comparación (optimizado)
curl "http://localhost:8000/api/v1/exercises/fonema_r_suave_1/features-comparison"

# Health check
curl "http://localhost:8000/api/v1/exercises/health"

# Estadísticas
curl "http://localhost:8000/api/v1/exercises/statistics"
```

## 🔄 Flujo de datos

```
HTTP Request
    ↓
FastAPI Route (exercise_routes.py)
    ↓
Controller (exercise_controller.py)
    ↓
Use Case (application layer)
    ↓
Repository Interface (domain layer)
    ↓
Repository Implementation (data layer)
    ↓
Database (PostgreSQL / MongoDB)
```

## 📝 Notas importantes

1. **Inyección de dependencias**: Usar `Depends()` de FastAPI para todas las dependencias.

2. **Manejo de errores**: Los controladores capturan excepciones y las convierten a HTTPException.

3. **Validación**: Validar en dos niveles:
   - Nivel HTTP (FastAPI + validators.py)
   - Nivel dominio (modelos de dominio)

4. **Conexiones**: Usar pools de conexión para PostgreSQL y cliente singleton para MongoDB.

5. **Índices**: Crear índices en MongoDB al iniciar la aplicación con `initialize_repositories()`.

## 🧪 Testing

Los repositorios pueden ser mockeados fácilmente gracias a la inversión de dependencias:

```python
# Mock del repositorio para testing
class MockExerciseRepository(ExerciseRepository):
    async def find_by_id(self, exercise_id):
        return Exercise(...)  # Retornar mock

# Inyectar mock en el controlador
controller = ExerciseController(
    get_exercises_use_case=MockGetExercisesUseCase()
)
```

## 📚 Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [Motor (MongoDB) Documentation](https://motor.readthedocs.io/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)

