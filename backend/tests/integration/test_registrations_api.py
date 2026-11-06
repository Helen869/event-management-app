from urllib.parse import quote

import pytest

EVENT = {"title": "Meetup", "starts_at": "2026-02-01T10:00:00Z", "max_capacity": 2}


@pytest.fixture
def event_id(client):
    return client.post("/api/events", json=EVENT).json()["id"]


def register(client, event_id, email):
    return client.post(f"/api/events/{event_id}/registrations", json={"email": email})


def registrations_url(event_id, email=None):
    url = f"/api/events/{event_id}/registrations"
    return url if email is None else f"{url}/{quote(email, safe='')}"


def test_register_returns_201_with_normalized_email(client, event_id):
    response = register(client, event_id, "  Alice@Example.COM ")

    assert response.status_code == 201
    assert response.json() == {
        "email": "alice@example.com",
        "registered_at": "2026-01-01T12:00:00Z",
    }


def test_event_counts_reflect_registrations(client, event_id):
    register(client, event_id, "a@example.com")

    event = client.get(f"/api/events/{event_id}").json()
    assert (event["registered_count"], event["remaining_seats"], event["is_full"]) == (1, 1, False)


def test_list_registrations_returns_attendees(client, event_id):
    register(client, event_id, "a@example.com")
    register(client, event_id, "b@example.com")

    response = client.get(registrations_url(event_id))

    assert response.status_code == 200
    assert [r["email"] for r in response.json()] == ["a@example.com", "b@example.com"]


def test_invalid_email_is_rejected_with_422(client, event_id):
    response = register(client, event_id, "not-an-email")

    assert response.status_code == 422
    assert response.json()["details"][0]["field"] == "email"


def test_duplicate_registration_returns_409(client, event_id):
    register(client, event_id, "alice@example.com")

    response = register(client, event_id, "ALICE@example.com")

    assert response.status_code == 409
    assert response.json()["code"] == "ALREADY_REGISTERED"


def test_full_event_returns_409(client, event_id):
    register(client, event_id, "a@example.com")
    register(client, event_id, "b@example.com")

    response = register(client, event_id, "c@example.com")

    assert response.status_code == 409
    assert response.json()["code"] == "EVENT_FULL"


def test_registration_for_past_event_returns_409(client, event_id, clock):
    clock.advance(days=31)

    response = register(client, event_id, "alice@example.com")

    assert response.status_code == 409
    assert response.json()["code"] == "EVENT_IN_PAST"


def test_registration_for_unknown_event_returns_404(client):
    response = register(client, "00000000-0000-4000-8000-000000000000", "a@example.com")

    assert response.status_code == 404
    assert response.json()["code"] == "EVENT_NOT_FOUND"


@pytest.mark.parametrize(
    "email",
    ["first.last+tag@example.com", "o'neil@example.com", "a/b@example.com"],
)
def test_unregister_with_percent_encoded_email_returns_204(client, event_id, email):
    register(client, event_id, email)

    response = client.delete(registrations_url(event_id, email))

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(registrations_url(event_id)).json() == []


def test_unregister_accepts_unencoded_plus_and_at(client, event_id):
    register(client, event_id, "first+tag@example.com")

    response = client.delete(f"{registrations_url(event_id)}/first+tag@example.com")

    assert response.status_code == 204


def test_unregister_unknown_email_returns_404(client, event_id):
    response = client.delete(registrations_url(event_id, "nobody@example.com"))

    assert response.status_code == 404
    assert response.json()["code"] == "REGISTRATION_NOT_FOUND"


def test_unregister_for_past_event_returns_409(client, event_id, clock):
    register(client, event_id, "alice@example.com")
    clock.advance(days=31)

    response = client.delete(registrations_url(event_id, "alice@example.com"))

    assert response.status_code == 409
    assert response.json()["code"] == "EVENT_IN_PAST"
