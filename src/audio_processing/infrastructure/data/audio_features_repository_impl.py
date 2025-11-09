"""
MongoDB implementation of AudioFeaturesRepository.

Implementa el puerto AudioFeaturesRepository usando MongoDB con motor.
"""

from typing import Optional, List, Dict
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from src.audio_processing.domain.models.audio_features import AudioFeatures
from src.audio_processing.domain.repositories.audio_features_repository import AudioFeaturesRepository


class AudioFeaturesRepositoryImpl(AudioFeaturesRepository):
    """
    Implementación de AudioFeaturesRepository usando MongoDB con motor.
    
    Colección: 'audio_features'
    """
    
    def __init__(self, mongo_client: AsyncIOMotorClient, db_name: str = "audio_processing"):
        self.db: AsyncIOMotorDatabase = mongo_client[db_name]
        self.collection = self.db.audio_features
    
    async def save(self, features: AudioFeatures) -> AudioFeatures:
        """Guarda features de audio (upsert)"""
        # El contrato dice 'features', así que usamos 'features'
        document = features.to_dict()
        
        await self.collection.update_one(
            {"_id": features.attempt_id},
            {"$set": document},
            upsert=True
        )
        
        return features
    
    async def find_by_attempt_id(self, attempt_id: str) -> Optional[AudioFeatures]:
        """Busca features por ID de intento"""
        document = await self.collection.find_one({"_id": attempt_id})
        return self._map_document_to_features(document) if document else None
    
    # --- MÉTODO ACTUALIZADO ---
    # Coincide con: find_by_user(self, user_id: str, limit: int = 20, offset: int = 0)
    async def find_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[AudioFeatures]:
        """Busca features por usuario, con paginación"""
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort("extracted_at", -1).skip(offset).limit(limit)
        
        documents = await cursor.to_list(length=limit)
        return [self._map_document_to_features(doc) for doc in documents]
    
    # --- MÉTODO ACTUALIZADO ---
    # Coincide con: find_by_exercise(self, exercise_id: str, limit: int = 100)
    async def find_by_exercise(
        self,
        exercise_id: str,
        limit: int = 100
    ) -> List[AudioFeatures]:
        """Busca features por ejercicio"""
        cursor = self.collection.find(
            {"exercise_id": exercise_id}
        ).sort("extracted_at", -1).limit(limit)
        
        documents = await cursor.to_list(length=limit)
        return [self._map_document_to_features(doc) for doc in documents]
    
    async def delete(self, attempt_id: str) -> bool:
        """Elimina features de un intento"""
        result = await self.collection.delete_one({"_id": attempt_id})
        return result.deleted_count > 0

    async def exists(self, attempt_id: str) -> bool:
        """Verifica si existen features para un attempt_id"""
        document = await self.collection.find_one(
            {"_id": attempt_id}, 
            {"_id": 1} # Projection para no traer datos innecesarios
        )
        return document is not None

    async def count_by_user(self, user_id: str) -> int:
        """Cuenta la cantidad de features (intentos) de un usuario"""
        count = await self.collection.count_documents({"user_id": user_id})
        return count
    
    async def get_storage_stats(self) -> dict:
        """Obtiene estadísticas de almacenamiento"""
        total_docs = await self.collection.count_documents({})
        
        # collStats es un comando de admin, puede fallar si no hay datos
        try:
            stats = await self.db.command("collStats", "audio_features")
        except Exception:
            stats = {} # Devolver vacío si falla (ej. colección no existe)
        
        return {
            "total_documents": total_docs,
            "total_size_bytes": stats.get("size", 0),
            "total_size_mb": round(stats.get("size", 0) / (1024 * 1024), 2),
            "avg_document_size_bytes": stats.get("avgObjSize", 0),
            "storage_size_bytes": stats.get("storageSize", 0),
            "indexes_count": stats.get("nindexes", 0)
        }

    # --- MÉTODO ACTUALIZADO ---
    # Coincide con: find_for_ml_training(self, exercise_id: Optional[str] = None, ...)
    async def find_for_ml_training(
        self,
        exercise_id: Optional[str] = None,
        min_quality_score: float = 7.0,
        limit: int = 1000
    ) -> List[AudioFeatures]:
        """Obtiene features de alta calidad para entrenar modelos ML."""
        
        # Construir el query de filtro
        query: Dict = {
            # Asumiendo que guardas un campo 'quality_score' en el documento
            "quality_score": {"$gte": min_quality_score}
        }
        
        if exercise_id:
            query["exercise_id"] = exercise_id
            
        cursor = self.collection.find(query).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        return [self._map_document_to_features(doc) for doc in documents]
    
    # --- Métodos de utilidad ---
    
    def _map_document_to_features(self, document: dict) -> AudioFeatures:
        """Convierte documento MongoDB a AudioFeatures"""
        return AudioFeatures.from_dict(document)
    
    async def create_indexes(self):
        """Crea índices necesarios (llamar al inicializar la app)"""
        await self.collection.create_index("user_id")
        await self.collection.create_index("exercise_id")
        await self.collection.create_index("extracted_at")
        await self.collection.create_index([("user_id", 1), ("extracted_at", -1)])
        
        # Índice para ML (calidad y ejercicio)
        await self.collection.create_index([
            ("exercise_id", 1), 
            ("quality_score", -1)
        ])

