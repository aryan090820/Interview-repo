class DomainError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404


class SlotUnavailableError(DomainError):
    status_code = 409


class InvalidRequestError(DomainError):
    status_code = 422


class QueryFailedError(DomainError):
    status_code = 422
