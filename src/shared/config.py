from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List

class Settings(BaseSettings):
    """
    Configuración de la aplicación.
    Lee variables de entorno desde .env y proporciona tipado y valores por defecto.
    """
    
    # --- Configuración general ---
    # Nombres que coinciden con tu .env
    SERVICE_NAME: str = "Audio Processing Service"
    SERVICE_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000  # Pydantic leerá "8001" del .env y lo convertirá a entero
    DEBUG: bool = False # No está en tu .env, usará el valor por defecto

    # --- PostgreSQL ---
    # Nombres que coinciden con tu .env
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "audio_processing"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    
    # Estas no están en tu .env, usarán los valores por defecto
    POSTGRES_MIN_POOL_SIZE: int = 5
    POSTGRES_MAX_POOL_SIZE: int = 20
    
    # --- MongoDB ---
    # Nombre que coincide con tu .env
    MONGODB_URL: str = "mongodb://localhost:27017"
    
    # Esta variable está comentada en tu .env, así que usará el valor por defecto
    MONGODB_DB: str = "audio_features_db"
    
    # No están en tu .env, usarán los valores por defecto
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_POOL_SIZE: int = 50
    
    # --- Redis ---
    # No están en tu .env (comentadas), usarán los valores por defecto
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # --- JWT ---
    # Nombres que coinciden con tu .env
    JWT_SECRET_KEY: str = "your-secret-key-change-this"
    JWT_ALGORITHM: str = "HS256"

    # --- CORS ---
    # No está en tu .env, usará el valor por defecto
    CORS_ORIGINS: List[str] = ["*"]
    
    # --- Configuración de Pydantic (LA SOLUCIÓN) ---
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        # Esto le dice a Pydantic:
        # "Si ves variables extra en el .env, simplemente ignóralas"
        extra='ignore' 
    )


# Instancia global de configuración
settings = Settings()