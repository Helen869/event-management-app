from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response

from app.api.schemas import (
    ErrorResponse,
    EventInput,
    EventResponse,
    RegistrationInput,
    RegistrationResponse,
)
from app.service import EventService

router = APIRouter(prefix="/api")


def get_service(request: Request) -> EventService:
    return request.app.state.service


Service = Annotated[EventService, Depends(get_service)]


def errors(*codes: int) -> dict[int | str, dict[str, Any]]:
    return {code: {"model": ErrorResponse} for code in codes}


@router.get("/events", tags=["events"])
def list_events(service: Service) -> list[EventResponse]:
    return [EventResponse.from_summary(s) for s in service.list_events()]


@router.get("/events/{event_id}", tags=["events"], responses=errors(404, 422))
def get_event(event_id: UUID, service: Service) -> EventResponse:
    return EventResponse.from_summary(service.get_event(event_id))


@router.post("/events", status_code=201, tags=["events"], responses=errors(422))
def create_event(body: EventInput, service: Service, response: Response) -> EventResponse:
    summary = service.create_event(**body.model_dump())
    response.headers["Location"] = f"/api/events/{summary.event.id}"
    return EventResponse.from_summary(summary)


@router.put("/events/{event_id}", tags=["events"], responses=errors(404, 409, 422))
def update_event(event_id: UUID, body: EventInput, service: Service) -> EventResponse:
    return EventResponse.from_summary(service.update_event(event_id, **body.model_dump()))


@router.get("/events/{event_id}/registrations", tags=["registrations"], responses=errors(404, 422))
def list_registrations(event_id: UUID, service: Service) -> list[RegistrationResponse]:
    return [RegistrationResponse.from_domain(r) for r in service.list_registrations(event_id)]


@router.post(
    "/events/{event_id}/registrations",
    status_code=201,
    tags=["registrations"],
    responses=errors(404, 409, 422),
)
def register(event_id: UUID, body: RegistrationInput, service: Service) -> RegistrationResponse:
    return RegistrationResponse.from_domain(service.register(event_id, body.email))


# ":path" keeps a percent-encoded "/" (legal in an email local part) inside the parameter.
@router.delete(
    "/events/{event_id}/registrations/{email:path}",
    status_code=204,
    tags=["registrations"],
    responses=errors(404, 409, 422),
)
def unregister(event_id: UUID, email: str, service: Service) -> None:
    service.unregister(event_id, email)
