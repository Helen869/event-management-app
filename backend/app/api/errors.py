import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.api.schemas import ErrorResponse, FieldError
from app.domain import errors

logger = logging.getLogger(__name__)

DOMAIN_ERRORS: dict[type[errors.DomainError], tuple[int, str]] = {
    errors.EventNotFoundError: (404, "EVENT_NOT_FOUND"),
    errors.RegistrationNotFoundError: (404, "REGISTRATION_NOT_FOUND"),
    errors.EventInPastError: (409, "EVENT_IN_PAST"),
    errors.EventFullError: (409, "EVENT_FULL"),
    errors.AlreadyRegisteredError: (409, "ALREADY_REGISTERED"),
    errors.CapacityBelowRegistrationsError: (409, "CAPACITY_BELOW_REGISTRATIONS"),
    errors.StartTimeInPastError: (422, "START_TIME_IN_PAST"),
}


def _error(status: int, code: str, message: str, details: list[FieldError] | None = None):
    body = ErrorResponse(code=code, message=message, details=details or [])
    return JSONResponse(status_code=status, content=body.model_dump())


async def handle_domain_error(request: Request, exc: errors.DomainError) -> JSONResponse:
    status, code = DOMAIN_ERRORS[type(exc)]
    # Single place for rejection logs so the service does not log at every raise site.
    logger.warning("Rule rejected %s %s: %s", request.method, request.url.path, code)
    return _error(status, code, exc.message)


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        FieldError(field=".".join(str(part) for part in err["loc"][1:]), message=err["msg"])
        for err in exc.errors()
    ]
    return _error(422, "VALIDATION_ERROR", "Some fields are missing or invalid.", details)


async def handle_http_error(request: Request, exc: HTTPException) -> JSONResponse:
    return _error(exc.status_code, f"HTTP_{exc.status_code}", str(exc.detail))


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _error(500, "INTERNAL_ERROR", "Something went wrong. Please try again.")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(errors.DomainError, handle_domain_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(HTTPException, handle_http_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
