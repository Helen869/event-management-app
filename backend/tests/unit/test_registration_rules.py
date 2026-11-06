from datetime import timedelta
from uuid import uuid4

import pytest

from app.domain.errors import (
    AlreadyRegisteredError,
    EventFullError,
    EventInPastError,
    EventNotFoundError,
    RegistrationNotFoundError,
)
from tests.conftest import NOW


@pytest.fixture
def event_id(service):
    return service.create_event("Meetup", "", NOW + timedelta(days=1), 2).event.id


def emails(service, event_id):
    return [r.email for r in service.list_registrations(event_id)]


def test_user_can_register_for_upcoming_event(service, event_id):
    registration = service.register(event_id, "alice@example.com")

    assert registration.email == "alice@example.com"
    assert registration.registered_at == NOW
    assert service.get_event(event_id).registered_count == 1


def test_email_is_stored_trimmed_and_lowercase(service, event_id):
    service.register(event_id, "  Alice@Example.COM ")

    assert emails(service, event_id) == ["alice@example.com"]


def test_registrations_are_listed_in_registration_order(service, event_id, clock):
    service.register(event_id, "first@example.com")
    clock.advance(minutes=1)
    service.register(event_id, "second@example.com")

    assert emails(service, event_id) == ["first@example.com", "second@example.com"]


def test_cannot_register_for_event_that_has_started(service, event_id, clock):
    clock.advance(days=2)

    with pytest.raises(EventInPastError):
        service.register(event_id, "alice@example.com")


def test_cannot_register_when_start_time_equals_now(service, event_id, clock):
    clock.advance(days=1)

    with pytest.raises(EventInPastError):
        service.register(event_id, "alice@example.com")


def test_last_seat_can_be_taken(service, event_id):
    service.register(event_id, "a@example.com")
    service.register(event_id, "b@example.com")

    summary = service.get_event(event_id)
    assert summary.is_full
    assert summary.remaining_seats == 0


def test_cannot_register_when_event_is_full(service, event_id):
    service.register(event_id, "a@example.com")
    service.register(event_id, "b@example.com")

    with pytest.raises(EventFullError):
        service.register(event_id, "c@example.com")
    assert service.get_event(event_id).registered_count == 2


def test_same_email_cannot_register_twice(service, event_id):
    service.register(event_id, "alice@example.com")

    with pytest.raises(AlreadyRegisteredError):
        service.register(event_id, "alice@example.com")


def test_duplicate_detected_regardless_of_case_and_whitespace(service, event_id):
    service.register(event_id, "alice@example.com")

    with pytest.raises(AlreadyRegisteredError):
        service.register(event_id, "  ALICE@Example.com  ")


def test_same_email_may_register_for_different_events(service, event_id):
    other_id = service.create_event("Other", "", NOW + timedelta(days=2), 2).event.id

    service.register(event_id, "alice@example.com")
    service.register(other_id, "alice@example.com")

    assert emails(service, other_id) == ["alice@example.com"]


def test_duplicate_is_reported_before_full_when_both_apply(service, event_id):
    service.register(event_id, "a@example.com")
    service.register(event_id, "b@example.com")

    with pytest.raises(AlreadyRegisteredError):
        service.register(event_id, "a@example.com")


def test_cannot_register_for_unknown_event(service):
    with pytest.raises(EventNotFoundError):
        service.register(uuid4(), "alice@example.com")


def test_listing_registrations_of_unknown_event_is_not_found(service):
    with pytest.raises(EventNotFoundError):
        service.list_registrations(uuid4())


def test_registered_user_can_unregister(service, event_id):
    service.register(event_id, "alice@example.com")

    service.unregister(event_id, "alice@example.com")

    assert emails(service, event_id) == []


def test_unregister_matches_email_regardless_of_case_and_whitespace(service, event_id):
    service.register(event_id, "alice@example.com")

    service.unregister(event_id, " Alice@EXAMPLE.com")

    assert emails(service, event_id) == []


def test_cancellation_frees_a_seat_for_another_user(service, event_id):
    service.register(event_id, "a@example.com")
    service.register(event_id, "b@example.com")

    service.unregister(event_id, "a@example.com")
    service.register(event_id, "c@example.com")

    assert emails(service, event_id) == ["b@example.com", "c@example.com"]


def test_user_can_reregister_after_cancelling(service, event_id):
    service.register(event_id, "alice@example.com")
    service.unregister(event_id, "alice@example.com")

    service.register(event_id, "alice@example.com")

    assert emails(service, event_id) == ["alice@example.com"]


def test_cancelling_unregistered_email_is_not_found(service, event_id):
    with pytest.raises(RegistrationNotFoundError):
        service.unregister(event_id, "nobody@example.com")


def test_cancelling_for_unknown_event_is_not_found(service):
    with pytest.raises(EventNotFoundError):
        service.unregister(uuid4(), "alice@example.com")


def test_cannot_cancel_registration_for_past_event(service, event_id, clock):
    service.register(event_id, "alice@example.com")
    clock.advance(days=1)

    with pytest.raises(EventInPastError):
        service.unregister(event_id, "alice@example.com")
    assert emails(service, event_id) == ["alice@example.com"]


def test_attendees_of_started_event_can_still_be_listed(service, event_id, clock):
    service.register(event_id, "alice@example.com")
    clock.advance(days=1)

    assert emails(service, event_id) == ["alice@example.com"]


def test_past_event_is_reported_before_missing_registration_on_cancel(service, event_id, clock):
    clock.advance(days=1)

    with pytest.raises(EventInPastError):
        service.unregister(event_id, "nobody@example.com")
