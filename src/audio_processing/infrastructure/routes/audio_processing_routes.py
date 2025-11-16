"""
Audio Processing Routes - Endpoints para procesamiento de audio con validación de progresión.
"""

from typing import Optional
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.audio_processing.infrastructure.helpers.dependencies import (
    get_audio_processing_controller
)
from src.audio_processing.infrastructure.controllers.audio_processing_controller import (
    AudioProcessingController
)
from src.shared.auth_dependency import get_current_user

from src.exercise_progression.application.services.exercise_progression_service import ExerciseProgressionService
from src.exercise_progression.infrastructure.helpers.dependencies import (
    get_exercise_progression_service,
    get_exercise_repository
)

logger = logging.getLogger(__name__)
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
        description="ID del ejercicio (ej: 'fonema_r_suave_1')",
        pattern="^[a-z0-9_]+$"
    )
    reference_text: Optional[str] = Field(
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
                "exercise_id": "fonema_r_suave_1",
                "reference_text": "cara",
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
        403: {"description": "Ejercicio bloqueado"},
        404: {"description": "Ejercicio no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)


# ============================================
# ENDPOINTS
# ============================================

@audio_processing_router.post(
    "/process",
    summary="Procesar audio del usuario con validación de progresión",
    description="""
    Procesa un audio completo del usuario y actualiza su progreso en el sistema de ejercicios.
    
    **Flujo:**
    1. Valida que el ejercicio existe
    2. Valida que el usuario tenga acceso (ejercicio desbloqueado)
    3. Valida la calidad del audio (SNR, ruido, clipping)
    4. Normaliza el audio
    5. Extrae features acústicos (MFCCs, prosody, rhythm)
    6. Envía al ML Analysis Service para obtener scores
    7. Guarda todo en PostgreSQL + MongoDB
    8. Actualiza progreso del usuario
    9. Desbloquea siguiente ejercicio si score >= 70
    
    **Validaciones de Progresión:**
    - El ejercicio debe estar desbloqueado (available o in_progress)
    - El ejercicio anterior debe estar completado (score >= 70)
    - Si está bloqueado → 403 Forbidden
    
    **Si se completa el ejercicio (score >= 70):**
    - Se desbloquea automáticamente el siguiente ejercicio
    - Se actualizan estrellas basado en score:
      - 70-79: 1 estrella ⭐
      - 80-89: 2 estrellas ⭐⭐
      - 90+: 3 estrellas ⭐⭐⭐
    - Se actualiza el progreso global del usuario
    """,
    response_description="Resultado del procesamiento con scores y progreso actualizado",
    status_code=200
)
async def process_audio(
    request: ProcessAudioRequestSchema,
    current_user: dict = Depends(get_current_user),
    controller: AudioProcessingController = Depends(get_audio_processing_controller),
    progression_service: ExerciseProgressionService = Depends(get_exercise_progression_service)
):
    """
    Endpoint principal: Procesar audio con validación de progresión lineal.
    
    Args:
        request: Datos del audio (audio_base64, exercise_id, reference_text, metadata)
        current_user: Usuario autenticado (inyectado por JWT)
        controller: Controller con use cases de audio processing
        progression_service: Servicio de progresión de ejercicios
    
    Returns:
        Dict con:
        - attempt_id: ID del intento
        - scores: Scores de ML (pronunciation, fluency, rhythm, overall)
        - quality_check: Validaciones de calidad del audio
        - progression: Info de progreso (stars, unlocked_next, next_exercise)
        - processing_time_ms: Tiempo de procesamiento
    
    Raises:
        HTTPException 404: Si el ejercicio no existe
        HTTPException 403: Si el ejercicio está bloqueado
        HTTPException 400: Si el audio no pasa validaciones de calidad
    """
    user_id = uuid.UUID(current_user["user_id"])
    
    # 1. Buscar el ejercicio por exercise_id string
    exercise_repo = get_exercise_repository()
    exercise = await exercise_repo.get_by_exercise_id(request.exercise_id)
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ejercicio '{request.exercise_id}' no encontrado"
        )
    
    # 2. Validar acceso al ejercicio (progresión lineal)
    has_access = await progression_service.can_access_exercise(user_id, exercise.id)
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ejercicio bloqueado. Debes completar el ejercicio anterior primero."
        )
    
    # 3. Determinar reference_text (usar el del request o el del ejercicio)
    reference_text = request.reference_text or exercise.text_content
    
    # 4. Procesar audio (validación de calidad + extracción de features + ML analysis)
    result = await controller.process_audio(
        audio_base64=request.audio_base64,
        exercise_id=request.exercise_id,
        user_id=str(user_id),
        metadata=request.metadata,
        reference_text=reference_text
    )
    
    # 5. Actualizar progreso de ejercicios
    # El controller devuelve {"success": True, "data": {...}}
    data = result.get("data", result)
    overall_score = data.get("scores", {}).get("overall", 0)
    
    if overall_score is not None and overall_score != 0:
        progression_result = await progression_service.record_attempt(
            user_id=user_id,
            exercise_id=exercise.id,
            overall_score=float(overall_score)
        )
        
        # 6. Agregar info de progresión al response
        data["progression"] = progression_result
    else:
        # Si no hay score (error en ML), no actualizar progresión
        data["progression"] = {
            "progress_updated": False,
            "status": "pending",
            "stars_earned": 0,
            "unlocked_next": False,
            "next_exercise": None
        }
    
    return result


@audio_processing_router.post(
    "/validate-quality",
    summary="Validar calidad de audio (sin procesar)",
    description="""
    Valida rápidamente la calidad de un audio sin procesarlo completamente.
    
    Útil para dar feedback instantáneo en la UI antes de enviar el audio
    al servidor para procesamiento completo.
    
    **Validaciones:**
    - SNR (Signal-to-Noise Ratio) >= 10 dB
    - Presencia de ruido de fondo
    - Clipping / distorsión
    - Duración del audio (entre 0.5 y 30 segundos)
    
    **No requiere autenticación** para permitir pruebas rápidas.
    """,
    response_description="Resultado de la validación con recomendaciones",
    status_code=200
)
async def validate_audio_quality(
    request: ValidateAudioRequestSchema,
    controller: AudioProcessingController = Depends(get_audio_processing_controller)
):
    """
    Endpoint: Validar calidad de audio sin procesarlo.
    
    Args:
        request: Audio a validar (audio_base64)
        controller: Controller con use cases
    
    Returns:
        Dict con:
        - is_valid: bool
        - quality_score: float (0-100)
        - issues: Lista de problemas detectados
        - recommendation: Recomendación para el usuario
    """
    return await controller.validate_audio_quality(
        audio_base64=request.audio_base64
    )


@audio_processing_router.get(
    "/health",
    summary="Health check del módulo de audio",
    description="Verifica que el módulo de procesamiento de audio esté funcionando correctamente",
    tags=["Health"],
    status_code=200
)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Dict con status del servicio
    """
    return {
        "success": True,
        "module": "audio_processing",
        "status": "healthy",
        "features": [
            "audio_quality_validation",
            "feature_extraction",
            "ml_integration",
            "exercise_progression"
        ]
    }