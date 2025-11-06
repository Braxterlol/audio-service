"""
Excepciones personalizadas para la aplicación.
"""


class AppException(Exception):
    """Excepción base de la aplicación"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseException(AppException):
    """Excepción relacionada con la base de datos"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class NotFoundException(AppException):
    """Excepción cuando no se encuentra un recurso"""
    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class ValidationException(AppException):
    """Excepción de validación"""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

