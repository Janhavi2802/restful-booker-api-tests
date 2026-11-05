"""Shared fixtures: environment config, auth token, API clients and test data cleanup."""
import os
from dataclasses import replace
from urllib.parse import urlparse

import pytest

from api.clients import AuthClient, BookingClient
from api.config import load_config
from api.data_factory import build_booking


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default=None,
        help="Environment from config/config.yaml: prod (default) or local (offline mock)",
    )


@pytest.fixture(scope="session")
def config(request):
    cfg = load_config(request.config.getoption("--env"))
    if cfg.name == "local":
        # Start the offline mock automatically so `pytest --env=local` just works.
        # With pytest-xdist each worker (gw0, gw1, ...) gets its own port.
        from mock_server.server import start_in_background

        url = urlparse(cfg.base_url)
        worker = os.getenv("PYTEST_XDIST_WORKER", "gw0")
        port = url.port + int(worker.removeprefix("gw") or 0)
        cfg = replace(cfg, base_url=f"{url.scheme}://{url.hostname}:{port}")
        server = start_in_background(url.hostname, port)
        yield cfg
        server.shutdown()
    else:
        yield cfg


@pytest.fixture(scope="session")
def auth_client(config):
    return AuthClient(config)


@pytest.fixture(scope="session")
def token(auth_client, config):
    response = auth_client.create_token(config.username, config.password)
    assert response.status_code == 200, f"Auth failed: {response.text}"
    tok = response.json().get("token")
    assert tok, f"No token returned: {response.text}"
    return tok


@pytest.fixture(scope="session")
def booking_client(config):
    """Unauthenticated client (GET/POST don't need a token)."""
    return BookingClient(config)


@pytest.fixture(scope="session")
def authed_booking_client(config, token):
    """Client that sends the auth token cookie on PUT/PATCH/DELETE."""
    return BookingClient(config, token=token)


@pytest.fixture
def created_booking(booking_client, authed_booking_client):
    """Creates a fresh booking for a test and deletes it afterwards (teardown)."""
    payload = build_booking()
    response = booking_client.create_booking(payload)
    assert response.status_code == 200, response.text
    booking_id = response.json()["bookingid"]

    yield booking_id, payload

    # Cleanup; ignore if the test already deleted it
    authed_booking_client.delete_booking(booking_id)
