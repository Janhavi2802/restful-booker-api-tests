"""Positive end-to-end flows: create, read, update, partial update, delete."""
import allure
import pytest

from api.data_factory import build_booking, load_data
from api.schema_validator import assert_schema

BOOKING_DATA = load_data("bookings.json")


@allure.feature("Booking")
@pytest.mark.smoke
def test_get_booking_ids_matches_schema(booking_client):
    response = booking_client.get_booking_ids()

    assert response.status_code == 200
    assert_schema(response.json(), "booking_ids.json")


@allure.feature("Booking")
@pytest.mark.regression
@pytest.mark.parametrize("case", BOOKING_DATA, ids=[c["id"] for c in BOOKING_DATA])
def test_create_booking_data_driven(booking_client, authed_booking_client, case):
    payload = case["payload"]

    response = booking_client.create_booking(payload)

    assert response.status_code == 200
    body = response.json()
    assert_schema(body, "create_booking_response.json")
    assert body["booking"] == payload

    # Read it back to confirm it was persisted, then clean up
    booking_id = body["bookingid"]
    fetched = booking_client.get_booking(booking_id)
    assert fetched.status_code == 200
    assert fetched.json() == payload
    authed_booking_client.delete_booking(booking_id)


@allure.feature("Booking")
@pytest.mark.smoke
def test_get_booking_by_id(booking_client, created_booking):
    booking_id, payload = created_booking

    response = booking_client.get_booking(booking_id)

    assert response.status_code == 200
    assert_schema(response.json(), "booking.json")
    assert response.json()["firstname"] == payload["firstname"]


@allure.feature("Booking")
@pytest.mark.regression
def test_filter_booking_ids_by_name(booking_client, created_booking):
    booking_id, payload = created_booking

    response = booking_client.get_booking_ids(
        firstname=payload["firstname"], lastname=payload["lastname"]
    )

    assert response.status_code == 200
    ids = [item["bookingid"] for item in response.json()]
    assert booking_id in ids


@allure.feature("Booking")
@pytest.mark.regression
def test_full_update_booking(authed_booking_client, booking_client, created_booking):
    booking_id, _ = created_booking
    new_payload = build_booking(firstname="Updated", additionalneeds="Dinner")

    response = authed_booking_client.update_booking(booking_id, new_payload)

    assert response.status_code == 200
    assert response.json() == new_payload
    assert booking_client.get_booking(booking_id).json() == new_payload


@allure.feature("Booking")
@pytest.mark.regression
@pytest.mark.parametrize(
    "patch",
    [
        pytest.param({"firstname": "Patched"}, id="firstname_only"),
        pytest.param({"totalprice": 4321}, id="price_only"),
        pytest.param({"depositpaid": False, "additionalneeds": "Dinner"}, id="two_fields"),
    ],
)
def test_partial_update_changes_only_given_fields(authed_booking_client, created_booking, patch):
    booking_id, original = created_booking

    response = authed_booking_client.partial_update_booking(booking_id, patch)

    assert response.status_code == 200
    expected = {**original, **patch}
    assert response.json() == expected


@allure.feature("Booking")
@pytest.mark.smoke
def test_delete_booking(authed_booking_client, booking_client, created_booking):
    booking_id, _ = created_booking

    response = authed_booking_client.delete_booking(booking_id)

    # Restful-Booker returns 201 Created on successful delete
    assert response.status_code == 201
    assert booking_client.get_booking(booking_id).status_code == 404
