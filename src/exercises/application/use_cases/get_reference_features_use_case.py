"""
GetReferenceFeaturesUseCase - Caso de uso para obtener features de referencia.
"""

from dataclasses import dataclass
from typing import Optional
from src.exercises.domain.models.reference_features import ReferenceFeatures
from src.exercises.domain.repositories.exercise_repository import ExerciseRepository
from src.exercises.domain.repositories.reference_features_repository import ReferenceFeaturesRepository


@dataclass
class GetReferenceFeaturesRequest:
    """DTO para la petición"""
    exercise_id: str


@dataclass
class GetReferenceFeaturesResponse:
    """DTO para la respuesta"""
    features: Optional[ReferenceFeatures]
    found: bool
    exercise_exists: bool
    
    def to_dict(self) -> dict:
        if not self.found or not self.features:
            return {
                "found": False,
                "exercise_exists": self.exercise_exists,
                "features": None
            }
        
        return {
            "found": True,
            "exercise_exists": True,
            "features": self.features.to_dict()
        }


class GetReferenceFeaturesUseCase:
    """
    Caso de uso: Obtener features precalculadas del audio de referencia.
    
    Verifica que el ejercicio exista antes de buscar las features.
    """
    
    def __init__(
        self,
        exercise_repository: ExerciseRepository,
        reference_features_repository: ReferenceFeaturesRepository
    ):
        self.exercise_repository = exercise_repository
        self.reference_features_repository = reference_features_repository
    
    async def execute(
        self,
        request: GetReferenceFeaturesRequest
    ) -> GetReferenceFeaturesResponse:
        """
        Ejecuta el caso de uso.
        
        Args:
            request: ID del ejercicio
        
        Returns:
            GetReferenceFeaturesResponse: Features encontradas o None
        
        Raises:
            ValueError: Si el exercise_id está vacío
        """
        # Validación
        if not request.exercise_id or not request.exercise_id.strip():
            raise ValueError("El exercise_id no puede estar vacío")
        
        exercise_id = request.exercise_id.strip()
        
        # Verificar que el ejercicio existe
        exercise = await self.exercise_repository.find_by_exercise_id(exercise_id)
        exercise_exists = exercise is not None
        
        if not exercise_exists:
            return GetReferenceFeaturesResponse(
                features=None,
                found=False,
                exercise_exists=False
            )
        
        # Buscar features de referencia
        features = await self.reference_features_repository.find_by_exercise_id(
            exercise_id
        )
        
        return GetReferenceFeaturesResponse(
            features=features,
            found=features is not None,
            exercise_exists=True
        )


class GetReferenceFeaturesForComparisonUseCase:
    """
    Caso de uso especializado: Obtener features optimizadas para comparación DTW.
    
    Retorna solo las features necesarias para comparación, reduciendo payload.
    """
    
    def __init__(
        self,
        reference_features_repository: ReferenceFeaturesRepository
    ):
        self.reference_features_repository = reference_features_repository
    
    async def execute(self, exercise_id: str) -> Optional[dict]:
        """
        Obtiene features optimizadas para comparación.
        
        Args:
            exercise_id: ID del ejercicio
        
        Returns:
            dict: Features esenciales para comparación o None
        """
        features = await self.reference_features_repository.find_by_exercise_id(
            exercise_id
        )
        
        if not features:
            return None
        
        # Retornar solo lo necesario para comparación
        return {
            "exercise_id": features.exercise_id,
            "mfcc_stats": {
                "mean": features.mfcc_stats.mean,
                "std": features.mfcc_stats.std
            },
            "prosody_stats": {
                "f0_mean": features.prosody_stats.f0_mean,
                "f0_std": features.prosody_stats.f0_std,
                "f0_range": features.prosody_stats.f0_range
            },
            "duration_seconds": features.duration_seconds,
            "normalization_params": features.normalization_params.to_dict() if hasattr(features.normalization_params, 'to_dict') else {
                "f0_range": features.normalization_params.f0_range,
                "mfcc_mean": features.normalization_params.mfcc_mean,
                "mfcc_std": features.normalization_params.mfcc_std
            },
            "thresholds": {
                "dtw_good": features.thresholds.dtw_good,
                "dtw_acceptable": features.thresholds.dtw_acceptable,
                "dtw_poor": features.thresholds.dtw_poor
            }
        }