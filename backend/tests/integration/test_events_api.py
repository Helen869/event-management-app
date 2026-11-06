import pytest
from fastapi.testclient import TestClient

from app.main import create_app

FUTURE = "2026-02-01T10:00:00+02:00"
EVENT = {"title": "Meetup", "description": "Monthly", "starts_at": FUTURE, "max_capacity": 3}
EVENT_FIELDS = {
    "id",
    "title",
    "description",
    "starts_at",
    "max_capacity",
    "registered_count",
    "remaining_seats",
    "is_past",
    "is_full",
}


def create_event(client, **overrides):
    response = client.post("/api/events", json=EVENT | overrides)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_event_returns_201_with_full_schema_and_location(client):
    response = client.post("/api/events", json=EVENT)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == EVENT_FIELDS
    assert body["starts_at"] == "2026-02-01T08:00:00Z"
    assert (body["registered_count"], body["remaining_seats"]) == (0, 3)
    assert (body["is_past"], body["is_full"]) == (False, False)
    assert response.headers["location"] == f"/api/events/{body['id']}"


def test_list_and_get_return_created_events(client):
    created = create_event(client)

    assert client.get("/api/events").json() == [created]
    assert client.get(f"/api/events/{created['id']}").json() == created


def test_update_event_returns_updated_event(client):
    event_id = create_event(client)["id"]
    changes = EVENT | {"title": "Renamed", "max_capacity": 10}

    response = client.put(f"/api/events/{event_id}", json=changes)

    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"
    assert response.json()["remaining_seats"] == 10


@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"title": "   "}, "title"),
        ({"title": "x" * 201}, "title"),
        ({"max_capacity": 0}, "max_capacity"),
        ({"max_capacity": -1}, "max_capacity"),
        ({"max_capacity": 100_001}, "max_capacity"),
        ({"max_capacity": 2.5}, "max_capacity"),
        ({"max_capacity": "5"}, "max_capacity"),
        ({"starts_at": "2026-02-01T10:00:00"}, "starts_at"),
        ({"starts_at": "not a date"}, "starts_at"),
        ({"unknown": "x"}, "unknown"),
    ],
)
def test_invalid_event_fields_are_rejected_with_field_details(client, overrides, field):
    response = client.post("/api/events", json=EVENT | overrides)

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert field in [d["field"] for d in body["details"]]


def test_missing_required_fields_are_listed(client):
    response = client.post("/api/events", json={})

    assert response.status_code == 422
    fields = {d["field"] for d in response.json()["details"]}
    assert fields == {"title", "starts_at", "max_capacity"}


def test_max_capacity_upper_bound_is_accepted(client):
    assert create_event(client, max_capacity=100_000)["max_capacity"] == 100_000


def test_event_in_the_past_is_rejected_with_422(client):
    response = client.post("/api/events", json=EVENT | {"starts_at": "2025-12-31T23:00:00Z"})

    assert response.status_code == 422
    assert response.json()["code"] == "START_TIME_IN_PAST"


def test_unknown_event_returns_404_error_body(client):
    response = client.get("/api/events/00000000-0000-4000-8000-000000000000")

    assert response.status_code == 404
    assert response.json() == {
        "code": "EVENT_NOT_FOUND",
        "message": "Event not found.",
        "details": [],
    }


def test_malformed_event_id_returns_422(client):
    response = client.get("/api/events/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["details"][0]["field"] == "event_id"


def test_updating_past_event_returns_409(client, clock):
    event_id = create_event(client)["id"]
    clock.advance(days=60)

    response = client.put(
        f"/api/events/{event_id}", json=EVENT | {"starts_at": "2026-12-01T10:00Z"}
    )

    assert response.status_code == 409
    assert response.json()["code"] == "EVENT_IN_PAST"


def test_reducing_capacity_below_registrations_returns_409(client):
    event_id = create_event(client)["id"]
    for email in ("a@example.com", "b@example.com"):
        client.post(f"/api/events/{event_id}/registrations", json={"email": email})

    response = client.put(f"/api/events/{event_id}", json=EVENT | {"max_capacity": 1})

    assert response.status_code == 409
    assert response.json()["code"] == "CAPACITY_BELOW_REGISTRATIONS"
    assert response.json()["message"] == (
        "Max capacity cannot be lower than the current 2 registrations."
    )


def test_unknown_route_uses_uniform_error_body(client):
    response = client.get("/api/nothing-here")

    assert response.status_code == 404
    assert response.json()["code"] == "HTTP_404"


def test_unexpected_error_returns_500_without_internal_details():
    class BrokenService:
        def list_events(self):
            raise RuntimeError("internal detail: db-host-17")

    client = TestClient(create_app(BrokenService()), raise_server_exceptions=False)

    response = client.get("/api/events")

    assert response.status_code == 500
    assert response.json()["code"] == "INTERNAL_ERROR"
    assert "db-host-17" not in response.text
