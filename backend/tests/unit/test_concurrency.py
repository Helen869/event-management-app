import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from app.domain.errors import EventFullError
from app.repository import InMemoryRepository
from app.service import EventService
from tests.conftest import NOW

CAPACITY = 10
ATTEMPTS = 50


class SlowCountRepository(InMemoryRepository):
    """Yields between the capacity read and the insert so a missing lock reliably shows a race.

    Without this, the GIL makes the race too rare for the test to prove anything.
    """

    def count_registrations(self, event_id):
        count = super().count_registrations(event_id)
        time.sleep(0.001)
        return count


def test_concurrent_registrations_never_exceed_capacity(clock):
    service = EventService(SlowCountRepository(), clock)
    event_id = service.create_event("Launch", "", NOW + timedelta(days=1), CAPACITY).event.id
    start = threading.Barrier(ATTEMPTS)

    def attempt(i: int) -> bool:
        start.wait()
        try:
            service.register(event_id, f"user{i}@example.com")
            return True
        except EventFullError:
            return False

    with ThreadPoolExecutor(max_workers=ATTEMPTS) as pool:
        outcomes = list(pool.map(attempt, range(ATTEMPTS)))

    assert outcomes.count(True) == CAPACITY
    assert len(service.list_registrations(event_id)) == CAPACITY
    assert service.get_event(event_id).remaining_seats == 0
