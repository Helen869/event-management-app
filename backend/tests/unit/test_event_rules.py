from datetime import timedelta, timezone
from uuid import uuid4

import pytest

from app.domain.errors import (
    CapacityBelowRegistrationsError,
    EventInPastError,
    EventNotFoundError,
    StartTimeInPastError,
)
from tests.conftest import NOW

TOMORROW = NOW + timedelta(days=1)


def create(service, starts_at=TOMORROW, max_capacity=10, title="Meetup"):
    return service.create_event(title, "", starts_at, max_capacity)


def update(service, event_id, starts_at=TOMORROW, max_capacity=10, title="Meetup"):
    return service.update_event(event_id, title, "", starts_at, max_capacity)


def test_new_event_starts_empty_with_all_seats_available(service):
    summary = create(service, max_capacity=5)

    assert summary.registered_count == 0
    assert summary.remaining_seats == 5
    assert not summary.is_full
    assert not summary.is_past


def test_event_start_time_is_stored_in_utc(service):
    plus_two = timezone(timedelta(hours=2))

    summary = create(service, starts_at=TOMORROW.astimezone(plus_two))

    assert summary.event.starts_at.utcoffset() == timedelta(0)
    assert summary.event.starts_at == TOMORROW


def test_cannot_create_event_in_the_past(service):
    with pytest.raises(StartTimeInPastError):
        create(service, starts_at=NOW - timedelta(minutes=1))


def test_cannot_create_event_starting_exactly_now(service):
    with pytest.raises(StartTimeInPastError):
        create(service, starts_at=NOW)


def test_events_are_listed_by_start_time(service):
    later = create(service, starts_at=NOW + timedelta(days=5), title="Later")
    sooner = create(service, starts_at=NOW + timedelta(days=1), title="Sooner")

    assert [s.event.id for s in service.list_events()] == [sooner.event.id, later.event.id]


def test_event_becomes_past_once_its_start_time_is_reached(service, clock):
    event = create(service, starts_at=NOW + timedelta(hours=1)).event

    clock.advance(hours=1)

    assert service.get_event(event.id).is_past


def test_getting_unknown_event_is_not_found(service):
    with pytest.raises(EventNotFoundError):
        service.get_event(uuid4())


def test_upcoming_event_can_be_updated(service):
    event = create(service).event
    new_start = NOW + timedelta(days=3)

    updated = service.update_event(event.id, "Renamed", "New text", new_start, 20).event

    assert (updated.title, updated.description, updated.starts_at, updated.max_capacity) == (
        "Renamed",
        "New text",
        new_start,
        20,
    )
    assert service.get_event(event.id).event == updated


def test_cannot_update_past_event(service, clock):
    event = create(service).event
    clock.advance(days=1)

    with pytest.raises(EventInPastError):
        update(service, event.id, starts_at=NOW + timedelta(days=7))


def test_cannot_move_event_into_the_past(service):
    event = create(service).event

    with pytest.raises(StartTimeInPastError):
        update(service, event.id, starts_at=NOW)


def test_cannot_reduce_capacity_below_registrations(service):
    event = create(service, max_capacity=5).event
    for i in range(3):
        service.register(event.id, f"user{i}@example.com")

    with pytest.raises(CapacityBelowRegistrationsError):
        update(service, event.id, max_capacity=2)


def test_capacity_can_be_reduced_to_exactly_current_registrations(service):
    event = create(service, max_capacity=5).event
    for i in range(3):
        service.register(event.id, f"user{i}@example.com")

    summary = update(service, event.id, max_capacity=3)

    assert summary.is_full
    assert summary.remaining_seats == 0


def test_updating_unknown_event_is_not_found(service):
    with pytest.raises(EventNotFoundError):
        update(service, uuid4())


def test_past_event_rejection_takes_precedence_over_invalid_new_date(service, clock):
    event = create(service).event
    clock.advance(days=2)

    with pytest.raises(EventInPastError):
        update(service, event.id, starts_at=NOW)


def test_past_new_date_is_reported_before_capacity_conflict(service):
    event = create(service, max_capacity=5).event
    service.register(event.id, "a@example.com")
    service.register(event.id, "b@example.com")

    with pytest.raises(StartTimeInPastError):
        update(service, event.id, starts_at=NOW, max_capacity=1)
