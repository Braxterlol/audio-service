"""
Audio Processing Routes - Endpoints para procesamiento de audio.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.audio_processing.infrastructure.helpers.dependencies import (
    get_audio_processing_controller
)
from src.audio_processing.infrastructure.controllers.audio_processing_controller import (
    AudioProcessingController
)
from src.shared.auth_dependency import get_current_user


# ============================================
# SCHEMAS PYDANTIC
# ============================================

class ProcessAudioRequestSchema(BaseModel):
    """Schema para procesar audio"""
    audio_base64: str = Field(
        ...,
        description="Audio codificado en base64 (formato WAV, MP3, etc.)",
        min_length=100
    )
    exercise_id: str = Field(
        ...,
        description="ID del ejercicio (ej: 'vocal_a_1')",
        pattern="^[a-z0-9_]+$"
    )
    reference_text: Optional[str] = Field(  # ← AGREGAR
        None,
        description="Texto de referencia para evaluación de pronunciación",
        max_length=500
    )
    metadata: Optional[dict] = Field(
        None,
        description="Información adicional del dispositivo"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_base64": "UklGRiQAAABXQVZFZm10...",
                "exercise_id": "fonema_rr_vibrante_2",
                "reference_text": "carro",  # ← AGREGAR
                "metadata": {
                    "device": "iPhone 13",
                    "app_version": "1.0.0",
                    "os": "iOS 16.5"
                }
            }
        }

class ValidateAudioRequestSchema(BaseModel):
    """Schema para validar calidad de audio"""
    audio_base64: str = Field(
        ...,
        description="Audio codificado en base64",
        min_length=100
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "audio_base64": "UklGRiQAAABXQVZFZm10..."
            }
        }


# ============================================
# ROUTER
# ============================================

audio_processing_router = APIRouter(
    prefix="/audio",
    tags=["Audio Processing"],
    responses={
        401: {"description": "No autenticado"},
        500: {"description": "Error interno del servidor"}
    }
)


# ============================================
# ENDPOINTS
# ============================================

@audio_processing_router.post(
    "/process",
    summary="Procesar audio del usuario",
    description="""
    Procesa un audio completo del usuario:
    
    1. Valida que el usuario puede intentar el ejercicio
    2. Valida la calidad del audio (SNR, ruido, clipping)
    3. Normaliza el audio
    4. Extrae features acústicos (MFCCs, prosody, rhythm)
    5. Guarda features en MongoDB
    6. Crea registro del intento en PostgreSQL
    7. Retorna métricas básicas
    
    **Nota:** Los scores finales (pronunciation, fluency, rhythm) se calculan
    posteriormente por el servicio de ML Analysis. Este endpoint solo retorna
    métricas básicas del audio.
    """,
    response_description="Resultado del procesamiento con métricas básicas",
    status_code=200
)
async def process_audio(
    request: ProcessAudioRequestSchema,
    current_user: dict = Depends(get_current_user),
    controller: AudioProcessingController = Depends(get_audio_processing_controller)
):
    """
    Endpoint principal: Procesar audio del usuario.
    
    Args:
        request: Datos del audio
        current_user: Usuario autenticado (inyectado por JWT)
        controller: Controller con use cases
    
    Returns:
        Resultado del procesamiento
    """
    user_id = current_user["user_id"]
    reference_text=request.reference_text
    
    return await controller.process_audio(
        audio_base64=request.audio_base64,
        exercise_id=request.exercise_id,
        user_id=user_id,
        metadata=request.metadata,
        reference_text=reference_text
    )


@audio_processing_router.post(
    "/validate-quality",
    summary="Validar calidad de audio (sin procesar)",
    description="""
    Valida rápidamente la calidad de un audio sin procesarlo completamente.
    
    Útil para dar feedback instantáneo en la UI antes de enviar el audio
    al servidor para procesamiento completo.
    
    Validaciones:
    - SNR (Signal-to-Noise Ratio)
    - Presencia de ruido de fondo
    - Clipping / distorsión
    - Duración del audio
    """,
    response_description="Resultado de la validación con recomendaciones",
    status_code=200
)
async def validate_audio_quality(
    request: ValidateAudioRequestSchema,
    controller: AudioProcessingController = Depends(get_audio_processing_controller)
):
    """
    Endpoint: Validar calidad de audio.
    
    Args:
        request: Audio a validar
        controller: Controller con use cases
    
    Returns:
        Resultado de la validación
    """
    return await controller.validate_audio_quality(
        audio_base64=request.audio_base64
    )


@audio_processing_router.get(
    "/health",
    summary="Health check del módulo de audio",
    description="Verifica que el módulo de procesamiento de audio esté funcionando",
    tags=["Health"],
    status_code=200
)
async def health_check():
    """Health check endpoint."""
    return {
        "success": True,
        "module": "audio_processing",
        "status": "healthy"
    }