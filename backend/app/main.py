import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app.api.errors import register_error_handlers
from app.api.routes import router
from app.repository import InMemoryRepository
from app.service import EventService

logger = logging.getLogger("app.requests")


async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %d %.1fms", request.method, request.url.path, response.status_code, elapsed_ms
    )
    return response


def create_app(service: EventService | None = None) -> FastAPI:
    app = FastAPI(title="Event Management API", version="1.0.0")
    app.state.service = service or EventService(InMemoryRepository())
    app.include_router(router)
    register_error_handlers(app)
    app.middleware("http")(log_requests)
    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
# Our middleware already logs each request with its duration; avoid a second access line.
logging.getLogger("uvicorn.access").disabled = True

app = create_app()
