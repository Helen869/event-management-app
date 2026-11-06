from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Event:
    id: UUID
    title: str
    description: str
    starts_at: datetime
    max_capacity: int


@dataclass(frozen=True)
class Registration:
    event_id: UUID
    email: str
    registered_at: datetime


@dataclass(frozen=True)
class EventSummary:
    event: Event
    registered_count: int
    is_past: bool

    @property
    def remaining_seats(self) -> int:
        return self.event.max_capacity - self.registered_count

    @property
    def is_full(self) -> bool:
        return self.remaining_seats <= 0
