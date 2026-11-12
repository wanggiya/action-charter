"""Shared action failure identity; historical names remain compatible."""


class InterfaceApiError(RuntimeError):
    """Raised when the bounded interface API cannot fulfill a request."""


TaskActionError = InterfaceApiError
