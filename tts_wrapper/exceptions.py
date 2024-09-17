class BaseException(Exception):
    pass


class SynthError(BaseException):
    pass


class ModuleNotInstalled(BaseException):
    def __init__(self, module: str) -> None:
        message = f'Required module "{module}" is not installed.'
        super().__init__(message)


class UnsupportedFileFormat(BaseException):
    def __init__(self, format: str, engine: str) -> None:
        message = f'Format "{format}" is not supported by engine {engine}.'
        super().__init__(message)


class ModelNotFound(BaseException):
    def __init__(self, model: str, error: str) -> None:
        message = f'Failed to initialize or download model "{model}": {error}'
        super().__init__(message)
