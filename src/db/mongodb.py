"""
Configuración y gestión de conexiones a MongoDB.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from src.shared.config import settings


class MongoDatabase:
    """
    Gestor de conexiones a MongoDB usando motor.
    """
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
    
    def connect(self):
        """
        Crea el cliente de MongoDB.
        """
        if self.client is None:
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE
            )
            print(f"✅ MongoDB cliente creado: {settings.MONGODB_URL}")
    
    def disconnect(self):
        """
        Cierra el cliente de MongoDB.
        """
        if self.client:
            self.client.close()
            self.client = None
            print("✅ MongoDB cliente cerrado")
    
    def get_client(self) -> AsyncIOMotorClient:
        """
        Obtiene el cliente de MongoDB.
        
        Returns:
            AsyncIOMotorClient: Cliente de MongoDB
        
        Raises:
            RuntimeError: Si el cliente no está inicializado
        """
        if self.client is None:
            raise RuntimeError("MongoDB cliente no está inicializado. Llamar a connect() primero.")
        return self.client


# Instancia global
mongo_db = MongoDatabase()

