import logging
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.errors import (
    AlreadyRegisteredError,
    CapacityBelowRegistrationsError,
    EventFullError,
    EventInPastError,
    EventNotFoundError,
    RegistrationNotFoundError,
    StartTimeInPastError,
)
from app.domain.models import Event, EventSummary, Registration
from app.repository import EventRepository

logger = logging.getLogger(__name__)

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_email(email: str) -> str:
    return email.strip().lower()


class EventService:
    """Enforces all business rules; each operation runs under the repository lock."""

    def __init__(self, repository: EventRepository, clock: Clock = utc_now) -> None:
        self._repo = repository
        self._clock = clock

    def list_events(self) -> list[EventSummary]:
        with self._repo.atomic():
            now = self._clock()
            events = sorted(self._repo.list_events(), key=lambda e: e.starts_at)
            return [self._summarize(event, now) for event in events]

    def get_event(self, event_id: UUID) -> EventSummary:
        with self._repo.atomic():
            return self._summarize(self._get_event(event_id), self._clock())

    def create_event(
        self, title: str, description: str, starts_at: datetime, max_capacity: int
    ) -> EventSummary:
        with self._repo.atomic():
            now = self._clock()
            if starts_at <= now:
                raise StartTimeInPastError()
            event = Event(uuid4(), title, description, starts_at.astimezone(UTC), max_capacity)
            self._repo.save_event(event)
            summary = self._summarize(event, now)
        logger.info("Event created id=%s max_capacity=%d", event.id, max_capacity)
        return summary

    def update_event(
        self,
        event_id: UUID,
        title: str,
        description: str,
        starts_at: datetime,
        max_capacity: int,
    ) -> EventSummary:
        with self._repo.atomic():
            now = self._clock()
            current = self._get_event(event_id)
            if current.starts_at <= now:
                raise EventInPastError()
            if starts_at <= now:
                raise StartTimeInPastError()
            registered = self._repo.count_registrations(event_id)
            if max_capacity < registered:
                raise CapacityBelowRegistrationsError(registered)
            event = Event(event_id, title, description, starts_at.astimezone(UTC), max_capacity)
            self._repo.save_event(event)
            summary = self._summarize(event, now)
        logger.info("Event updated id=%s", event_id)
        return summary

    def list_registrations(self, event_id: UUID) -> list[Registration]:
        with self._repo.atomic():
            self._get_event(event_id)
            return self._repo.list_registrations(event_id)

    def register(self, event_id: UUID, email: str) -> Registration:
        email = normalize_email(email)
        with self._repo.atomic():
            now = self._clock()
            event = self._get_event(event_id)
            if event.starts_at <= now:
                raise EventInPastError("Registration is closed because this event has started.")
            # Duplicate is checked before capacity: "already registered" is the more accurate
            # answer when both apply.
            if self._repo.has_registration(event_id, email):
                raise AlreadyRegisteredError()
            if self._repo.count_registrations(event_id) >= event.max_capacity:
                raise EventFullError()
            registration = Registration(event_id, email, now)
            self._repo.add_registration(registration)
        logger.info("Registration created event_id=%s", event_id)
        return registration

    def unregister(self, event_id: UUID, email: str) -> None:
        email = normalize_email(email)
        with self._repo.atomic():
            event = self._get_event(event_id)
            if event.starts_at <= self._clock():
                raise EventInPastError(
                    "Registrations cannot be cancelled because this event has started."
                )
            if not self._repo.remove_registration(event_id, email):
                raise RegistrationNotFoundError()
        logger.info("Registration cancelled event_id=%s", event_id)

    def _get_event(self, event_id: UUID) -> Event:
        event = self._repo.get_event(event_id)
        if event is None:
            raise EventNotFoundError()
        return event

    def _summarize(self, event: Event, now: datetime) -> EventSummary:
        return EventSummary(
            event=event,
            registered_count=self._repo.count_registrations(event.id),
            is_past=event.starts_at <= now,
        )
