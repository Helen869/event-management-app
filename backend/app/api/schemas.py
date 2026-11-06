from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.domain.models import EventSummary, Registration

MAX_CAPACITY_LIMIT = 100_000


class EventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    description: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] = ""
    starts_at: AwareDatetime
    # strict: reject "10", 10.0 and true instead of silently coercing them.
    max_capacity: int = Field(ge=1, le=MAX_CAPACITY_LIMIT, strict=True)


class RegistrationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class EventResponse(BaseModel):
    id: UUID
    title: str
    description: str
    starts_at: datetime
    max_capacity: int
    registered_count: int
    remaining_seats: int
    is_past: bool
    is_full: bool

    @classmethod
    def from_summary(cls, summary: EventSummary) -> "EventResponse":
        event = summary.event
        return cls(
            id=event.id,
            title=event.title,
            description=event.description,
            starts_at=event.starts_at,
            max_capacity=event.max_capacity,
            registered_count=summary.registered_count,
            remaining_seats=summary.remaining_seats,
            is_past=summary.is_past,
            is_full=summary.is_full,
        )


class RegistrationResponse(BaseModel):
    email: str
    registered_at: datetime

    @classmethod
    def from_domain(cls, registration: Registration) -> "RegistrationResponse":
        return cls(email=registration.email, registered_at=registration.registered_at)


class FieldError(BaseModel):
    field: str
    message: str


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: list[FieldError] = []
