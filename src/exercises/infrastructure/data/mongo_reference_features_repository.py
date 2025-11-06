"""
MongoDB implementation of ReferenceFeaturesRepository.

Implementa el puerto ReferenceFeaturesRepository usando MongoDB con motor.
"""

from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.exercises.domain.models.reference_features import (
    ReferenceFeatures,
    MFCCStats,
    ProsodyStats,
    PhonemeSegment,
    NormalizationParams,
    ComparisonThresholds
)
from src.exercises.domain.repositories.reference_features_repository import (
    ReferenceFeaturesRepository
)


class MongoReferenceFeaturesRepository(ReferenceFeaturesRepository):
    """
    Implementación de ReferenceFeaturesRepository usando MongoDB.
    
    Colección: 'reference_features'
    Índice: exercise_id (único)
    """
    
    def __init__(self, mongo_client: AsyncIOMotorClient, db_name: str = "audio_processing"):
        """
        Args:
            mongo_client: Cliente de MongoDB (motor)
            db_name: Nombre de la base de datos
        """
        self.db: AsyncIOMotorDatabase = mongo_client[db_name]
        self.collection = self.db.reference_features
    
    async def find_by_exercise_id(self, exercise_id: str) -> Optional[ReferenceFeatures]:
        """Obtiene features por exercise_id"""
        document = await self.collection.find_one({"exercise_id": exercise_id})
        
        if not document:
            return None
        
        return self._map_document_to_features(document)
    
    async def save(self, features: ReferenceFeatures) -> ReferenceFeatures:
        """Guarda features (upsert)"""
        document = features.to_dict()
        
        # Upsert: actualiza si existe, inserta si no
        await self.collection.update_one(
            {"exercise_id": features.exercise_id},
            {"$set": document},
            upsert=True
        )
        
        return features
    
    async def exists(self, exercise_id: str) -> bool:
        """Verifica si existen features"""
        count = await self.collection.count_documents(
            {"exercise_id": exercise_id},
            limit=1
        )
        return count > 0
    
    async def delete(self, exercise_id: str) -> bool:
        """Elimina features"""
        result = await self.collection.delete_one({"exercise_id": exercise_id})
        return result.deleted_count > 0
    
    async def find_all_cached(self) -> List[ReferenceFeatures]:
        """Obtiene todas las features cacheadas"""
        cursor = self.collection.find({})
        documents = await cursor.to_list(length=None)
        
        return [self._map_document_to_features(doc) for doc in documents]
    
    async def count_cached(self) -> int:
        """Cuenta features cacheadas"""
        return await self.collection.count_documents({})
    
    async def invalidate_cache(self, exercise_id: str) -> bool:
        """Invalida caché (elimina)"""
        return await self.delete(exercise_id)
    
    def _map_document_to_features(self, document: dict) -> ReferenceFeatures:
        """Convierte documento MongoDB a ReferenceFeatures"""
        # Usar el método from_dict del modelo
        return ReferenceFeatures.from_dict(document)
    
    async def create_indexes(self):
        """Crea índices necesarios (llamar al inicializar la app)"""
        # Índice único en exercise_id
        await self.collection.create_index("exercise_id", unique=True)
        
        # Índice en cache_version para posibles migraciones
        await self.collection.create_index("cache_version")
        
        # Índice en cached_at para limpiezas periódicas
        await self.collection.create_index("cached_at")

