"""
Script de precálculo de reference features para todos los ejercicios.

Uso:
    python scripts/precompute_reference_features.py
"""

import asyncio
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path
import tempfile
import requests

# Agregar src al path
sys.path.append(str(Path(__file__).parent.parent))

# ✅ CAMBIO: Importar tus gestores de DB
from src.db.mongodb import mongo_db
from src.db.postgres import postgres_db
from scripts.audio_feature_calculator import AudioFeatureCalculator


class ReferenceFeaturePrecomputer:
    """
    Precomputador de features de referencia.
    """
    
    def __init__(self):
        self.calculator = AudioFeatureCalculator()
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
    
    async def get_exercises_from_db(
        self,
        category: str = None,
        limit: int = None
    ):
        """Obtiene ejercicios de PostgreSQL"""
        # ✅ CAMBIO: Usar tu pool
        pool = postgres_db.get_pool()
        
        query = """
            SELECT id, exercise_id, category, subcategory, 
                   text_content, reference_audio_s3_url 
            FROM exercises 
            WHERE is_active = true
        """
        params = []
        
        if category:
            query += " AND category = $1"
            params.append(category)
        
        if limit:
            query += f" ORDER BY exercise_id LIMIT ${len(params) + 1}"
            params.append(limit)
        else:
            query += " ORDER BY exercise_id"
        
        # Ejecutar query
        async with pool.acquire() as conn:
            if params:
                rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)
        
        return rows
    
    async def feature_exists_in_mongodb(self, exercise_id: str) -> bool:
        """Verifica si ya existen features en MongoDB"""
        # ✅ CAMBIO: Usar tu cliente
        client = mongo_db.get_client()
        db = client["audio_features_db"]
        collection = db["reference_features_cache"]
        
        existing = await collection.find_one({"exercise_id": exercise_id})
        
        return existing is not None
    
    async def save_features_to_mongodb(self, exercise_id: str, features: dict):
        """Guarda features en MongoDB"""
        # ✅ CAMBIO: Usar tu cliente
        client = mongo_db.get_client()
        db = client["audio_features_db"]
        collection = db["reference_features_cache"]
        
        document = {
            "exercise_id": exercise_id,
            **features,
            "cache_version": "v1.0",
            "cached_at": datetime.utcnow()
        }
        
        # Upsert (insert o update)
        await collection.update_one(
            {"exercise_id": exercise_id},
            {"$set": document},
            upsert=True
        )
    
    def download_audio_from_s3(self, s3_url: str) -> str:
        """
        Descarga audio de S3 a un archivo temporal.
        """
        print(f"  📥 Descargando audio desde S3...")
        
        response = requests.get(s3_url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)
        
        temp_file.close()
        
        print(f"     ✅ Audio descargado: {temp_file.name}")
        
        return temp_file.name
    
    async def process_exercise(
        self,
        exercise: dict,
        force_recompute: bool = False
    ) -> bool:
        """
        Procesa un ejercicio y calcula sus features.
        """
        exercise_id = exercise['exercise_id']
        
        print(f"\n{'='*70}")
        print(f"🎯 Procesando: {exercise_id}")
        print(f"   Categoría: {exercise['category']}")
        print(f"   Texto: '{exercise['text_content']}'")
        print(f"{'='*70}")
        
        # Verificar si ya existe
        if not force_recompute:
            exists = await self.feature_exists_in_mongodb(exercise_id)
            if exists:
                print(f"⏭️  SKIPPED: Features ya existen para {exercise_id}")
                self.skipped_count += 1
                return True
        
        try:
            # Descargar audio de S3
            audio_path = self.download_audio_from_s3(exercise['reference_audio_s3_url'])
            
            # Calcular features
            features = self.calculator.calculate_all_features(
                audio_path,
                exercise['text_content']
            )
            
            # Guardar en MongoDB
            print(f"  💾 Guardando en MongoDB...")
            await self.save_features_to_mongodb(exercise_id, features)
            
            # Limpiar archivo temporal
            os.unlink(audio_path)
            
            print(f"✅ SUCCESS: Features guardadas para {exercise_id}")
            self.processed_count += 1
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR procesando {exercise_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            self.failed_count += 1
            return False
    
    async def run(
        self,
        category: str = None,
        limit: int = None,
        force_recompute: bool = False
    ):
        """
        Ejecuta el precálculo de features.
        """
        print("\n" + "="*70)
        print("🚀 INICIANDO PRECÁLCULO DE REFERENCE FEATURES")
        print("="*70)
        
        if category:
            print(f"📂 Categoría: {category}")
        if limit:
            print(f"🔢 Límite: {limit} ejercicios")
        if force_recompute:
            print(f"🔄 Modo: RECALCULAR TODO (force_recompute=True)")
        
        print("\n")
        
        # ✅ CAMBIO: Conectar a las bases de datos primero
        print("🔌 Conectando a bases de datos...")
        await postgres_db.connect()
        mongo_db.connect()
        print("✅ Conexiones establecidas\n")
        
        try:
            # Obtener ejercicios de la BD
            print("📖 Obteniendo ejercicios de PostgreSQL...")
            exercises = await self.get_exercises_from_db(category, limit)
            
            print(f"✅ {len(exercises)} ejercicios encontrados\n")
            
            if len(exercises) == 0:
                print("⚠️  No se encontraron ejercicios con los filtros especificados")
                return
            
            # Procesar cada ejercicio
            for i, exercise in enumerate(exercises, 1):
                print(f"\n[{i}/{len(exercises)}]")
                await self.process_exercise(exercise, force_recompute)
            
            # Resumen final
            print("\n" + "="*70)
            print("📊 RESUMEN FINAL")
            print("="*70)
            print(f"✅ Procesados exitosamente: {self.processed_count}")
            print(f"⏭️  Omitidos (ya existían): {self.skipped_count}")
            print(f"❌ Fallidos: {self.failed_count}")
            print(f"📊 Total: {len(exercises)}")
            
            if self.failed_count > 0:
                print(f"\n⚠️  ATENCIÓN: {self.failed_count} ejercicios fallaron")
            
            print("="*70 + "\n")
        
        finally:
            # ✅ CAMBIO: Cerrar conexiones al finalizar
            print("\n🔌 Cerrando conexiones...")
            await postgres_db.disconnect()
            mongo_db.disconnect()
            print("✅ Conexiones cerradas")


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Precalcula reference features para ejercicios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python scripts/precompute_reference_features.py
  python scripts/precompute_reference_features.py --category fonema
  python scripts/precompute_reference_features.py --limit 5
  python scripts/precompute_reference_features.py --force
        """
    )
    parser.add_argument(
        '--category',
        type=str,
        choices=['fonema', 'ritmo', 'entonacion'],
        help='Filtrar por categoría'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Límite de ejercicios a procesar'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Forzar recálculo aunque ya existan features'
    )
    
    args = parser.parse_args()
    
    try:
        precomputer = ReferenceFeaturePrecomputer()
        await precomputer.run(
            category=args.category,
            limit=args.limit,
            force_recompute=args.force
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())