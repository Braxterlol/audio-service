"""
Puertos (interfaces) de repositorios del dominio de audio_processing.
"""

from .attempt_repository import AttemptRepository
from .audio_features_repository import AudioFeaturesRepository
from .phoneme_error_repository import PhonemeErrorRepository
from .progress_repository import ProgressRepository
__all__ = [
    'AttemptRepository',
    'AudioFeaturesRepository',
    'PhonemeErrorRepository',
    'ProgressRepository'
]