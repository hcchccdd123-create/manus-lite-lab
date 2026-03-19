class AppError(Exception):
    code = 'APP_ERROR'

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    code = 'NOT_FOUND'


class ValidationError(AppError):
    code = 'VALIDATION_ERROR'


class ProviderError(AppError):
    code = 'PROVIDER_ERROR'


class ProviderAuthError(ProviderError):
    code = 'PROVIDER_AUTH_ERROR'


class ProviderRateLimitError(ProviderError):
    code = 'PROVIDER_RATE_LIMIT'


class ProviderTimeoutError(ProviderError):
    code = 'PROVIDER_TIMEOUT'


class ProviderUnavailableError(ProviderError):
    code = 'PROVIDER_UNAVAILABLE'


class RAGError(AppError):
    code = 'RAG_ERROR'


class RAGUnavailableError(RAGError):
    code = 'RAG_UNAVAILABLE'
