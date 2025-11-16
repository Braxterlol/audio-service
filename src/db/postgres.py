"""
Configuración y gestión de conexiones a PostgreSQL.
"""

import asyncpg
from typing import Optional
from src.shared.config import settings


class PostgresDatabase:
    """
    Gestor de conexiones a PostgreSQL usando asyncpg.
    """
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """
        Crea el pool de conexiones a PostgreSQL.
        """
        # Cerrar pool existente si hay (para forzar refresh de metadata)
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            print("🔄 Pool anterior cerrado, recreando...")
        
        self.pool = await asyncpg.create_pool(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            min_size=settings.POSTGRES_MIN_POOL_SIZE,
            max_size=settings.POSTGRES_MAX_POOL_SIZE,
            command_timeout=60
        )
        print(f"✅ PostgreSQL pool creado: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    
    async def disconnect(self):
        """
        Cierra el pool de conexiones.
        """
        if self.pool:
            await self.pool.close()
            self.pool = None
            print("✅ PostgreSQL pool cerrado")
    
    def get_pool(self) -> asyncpg.Pool:
        """
        Obtiene el pool de conexiones.
        
        Returns:
            asyncpg.Pool: Pool de conexiones
        
        Raises:
            RuntimeError: Si el pool no está inicializado
        """
        if self.pool is None:
            raise RuntimeError("PostgreSQL pool no está inicializado. Llamar a connect() primero.")
        return self.pool


# Instancia global
postgres_db = PostgresDatabase()

