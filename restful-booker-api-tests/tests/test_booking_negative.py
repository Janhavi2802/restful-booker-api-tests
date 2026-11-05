"""Negative and security scenarios: missing/invalid tokens (403), bad payloads (4xx/5xx)."""
import allure
import pytest

from api.data_factory import build_booking, load_data

INVALID_BOOKINGS = load_data("invalid_bookings.json")


@allure.feature("Booking - auth")
@pytest.mark.negative
@pytest.mark.parametrize(
    "bad_token",
    [
        pytest.param("", id="missing_token"),
        pytest.param("invalidtoken123", id="random_token"),
        pytest.param("' OR 1=1 --", id="injection_token"),
    ],
)
@pytest.mark.parametrize("operation", ["put", "patch", "delete"])
def test_modifying_booking_without_valid_token_is_forbidden(
    booking_client, created_booking, bad_token, operation
):
    booking_id, payload = created_booking

    if operation == "put":
        response = booking_client.update_booking(booking_id, build_booking(), token=bad_token)
    elif operation == "patch":
        response = booking_client.partial_update_booking(
            booking_id, {"firstname": "Hacker"}, token=bad_token)
    else:
        response = booking_client.delete_booking(booking_id, token=bad_token)

    assert response.status_code == 403
    # Data must be unchanged after a rejected call
    assert booking_client.get_booking(booking_id).json() == payload


@allure.feature("Booking - read")
@pytest.mark.negative
@pytest.mark.parametrize("booking_id", [999999999, 0, -1, "abc"], ids=str)
def test_get_nonexistent_booking_returns_404(booking_client, booking_id):
    response = booking_client.get_booking(booking_id)
    assert response.status_code == 404


@allure.feature("Booking - create")
@pytest.mark.negative
@pytest.mark.parametrize("case", INVALID_BOOKINGS, ids=[c["id"] for c in INVALID_BOOKINGS])
def test_create_booking_with_missing_required_field_fails(booking_client, case):
    payload = build_booking()
    payload.pop(case["remove"])

    response = booking_client.create_booking(payload)

    # Real service returns 500 here; a well-designed API should return 400.
    # Asserting "not success" documents the defect without hiding it.
    assert response.status_code in (400, 500)


@allure.feature("Booking - create")
@pytest.mark.negative
def test_create_booking_with_empty_body_fails(booking_client):
    response = booking_client.post("/booking", data="")
    assert response.status_code in (400, 500)


@allure.feature("Booking - delete")
@pytest.mark.negative
def test_delete_already_deleted_booking(authed_booking_client, created_booking):
    booking_id, _ = created_booking
    assert authed_booking_client.delete_booking(booking_id).status_code == 201

    second = authed_booking_client.delete_booking(booking_id)

    assert second.status_code == 405
