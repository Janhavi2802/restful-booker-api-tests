import allure
import pytest


@allure.feature("Health")
@pytest.mark.smoke
def test_ping_returns_201(booking_client):
    response = booking_client.ping()
    assert response.status_code == 201


@allure.feature("Health")
@pytest.mark.smoke
def test_ping_responds_quickly(booking_client, config):
    response = booking_client.ping()
    # Generous SLA for a free hosted service; tighten for real projects
    assert response.elapsed.total_seconds() < config.timeout
