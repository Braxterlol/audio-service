"""
Auth Dependency - Helper para extraer usuario del token JWT.

TEMPORAL: Mock para desarrollo hasta integrar el servicio de autenticación real.
"""

from typing import Dict
from fastapi import Header, HTTPException, status


async def get_current_user(
    authorization: str = Header(None)
) -> Dict:
    """
    Dependency para obtener el usuario actual desde el token JWT.
    
    TEMPORAL: Mock que retorna un usuario de prueba.
    TODO: Reemplazar con validación JWT real cuando integres el servicio de auth.
    
    Args:
        authorization: Header Authorization con token Bearer
    
    Returns:
        Dict con información del usuario de prueba
    """
    # Mock temporal - usuario de prueba
    # En producción, aquí decodificarías el JWT y extraerías el user_id
    
    # Si quieres simular que NO hay token:
    # if not authorization:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="No se proporcionó token de autenticación",
    #         headers={"WWW-Authenticate": "Bearer"}
    #     )
    
    # Por ahora, retornar un usuario mock para testing
    return {
        "user_id": "00000000-0000-0000-0000-000000000001",  # UUID de prueba
        "email": "test@example.com",
        "role": "user",
        "name": "Usuario de Prueba"
    }


async def get_current_user_optional(
    authorization: str = Header(None)
) -> Dict | None:
    """
    Dependency opcional - retorna None si no hay token.
    Útil para endpoints que pueden funcionar con o sin autenticación.
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


# ========================================
# VERSIÓN REAL (para cuando integres auth)
# ========================================

# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# import jwt
# from jwt.exceptions import InvalidTokenError
# import os
#
# security = HTTPBearer()
#
# async def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ) -> Dict:
#     """
#     Dependency para obtener el usuario actual desde el token JWT.
#     """
#     token = credentials.credentials
#     
#     try:
#         # Obtener secret key del .env
#         secret_key = os.getenv("JWT_SECRET_KEY")
#         algorithm = os.getenv("JWT_ALGORITHM", "HS256")
#         
#         if not secret_key:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="JWT_SECRET_KEY no configurado"
#             )
#         
#         # Decodificar token
#         payload = jwt.decode(
#             token,
#             secret_key,
#             algorithms=[algorithm]
#         )
#         
#         # Extraer información del usuario
#         user_id = payload.get("sub")
#         email = payload.get("email")
#         role = payload.get("role", "user")
#         
#         if not user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Token inválido: falta user_id"
#             )
#         
#         return {
#             "user_id": user_id,
#             "email": email,
#             "role": role,
#             "token_payload": payload
#         }
#     
#     except InvalidTokenError as e:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Token inválido: {str(e)}",
#             headers={"WWW-Authenticate": "Bearer"}
#         )