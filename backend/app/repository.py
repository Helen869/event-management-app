import threading
from contextlib import AbstractContextManager
from typing import Protocol
from uuid import UUID

from app.domain.models import Event, Registration


class EventRepository(Protocol):
    def atomic(self) -> AbstractContextManager[object]: ...
    def save_event(self, event: Event) -> None: ...
    def get_event(self, event_id: UUID) -> Event | None: ...
    def list_events(self) -> list[Event]: ...
    def add_registration(self, registration: Registration) -> None: ...
    def remove_registration(self, event_id: UUID, email: str) -> bool: ...
    def has_registration(self, event_id: UUID, email: str) -> bool: ...
    def list_registrations(self, event_id: UUID) -> list[Registration]: ...
    def count_registrations(self, event_id: UUID) -> int: ...


class InMemoryRepository:
    """Process-local storage; callers hold atomic() across check-then-write sequences."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[UUID, Event] = {}
        # Keyed by normalized email: O(1) duplicate checks, insertion order = registration order.
        self._registrations: dict[UUID, dict[str, Registration]] = {}

    def atomic(self) -> AbstractContextManager[object]:
        return self._lock

    def save_event(self, event: Event) -> None:
        self._events[event.id] = event
        self._registrations.setdefault(event.id, {})

    def get_event(self, event_id: UUID) -> Event | None:
        return self._events.get(event_id)

    def list_events(self) -> list[Event]:
        return list(self._events.values())

    def add_registration(self, registration: Registration) -> None:
        self._registrations[registration.event_id][registration.email] = registration

    def remove_registration(self, event_id: UUID, email: str) -> bool:
        return self._registrations[event_id].pop(email, None) is not None

    def has_registration(self, event_id: UUID, email: str) -> bool:
        return email in self._registrations[event_id]

    def list_registrations(self, event_id: UUID) -> list[Registration]:
        return list(self._registrations[event_id].values())

    def count_registrations(self, event_id: UUID) -> int:
        return len(self._registrations[event_id])
