"""Service clients for Restful-Booker endpoints."""
import allure

from api.base_client import BaseClient


class AuthClient(BaseClient):
    @allure.step("Create auth token")
    def create_token(self, username: str, password: str):
        return self.post("/auth", json={"username": username, "password": password})


class BookingClient(BaseClient):
    def __init__(self, config, token: str | None = None):
        super().__init__(config)
        self.token = token

    def _auth_headers(self, token: str | None = None) -> dict:
        tok = token if token is not None else self.token
        return {"Cookie": f"token={tok}"} if tok else {}

    @allure.step("Health check")
    def ping(self):
        return self.get("/ping")

    @allure.step("Get booking ids")
    def get_booking_ids(self, **filters):
        return self.get("/booking", params=filters or None)

    @allure.step("Get booking {booking_id}")
    def get_booking(self, booking_id):
        return self.get(f"/booking/{booking_id}")

    @allure.step("Create booking")
    def create_booking(self, payload: dict):
        return self.post("/booking", json=payload)

    @allure.step("Update booking {booking_id}")
    def update_booking(self, booking_id, payload: dict, token: str | None = None):
        return self.put(f"/booking/{booking_id}", json=payload,
                        headers=self._auth_headers(token))

    @allure.step("Partially update booking {booking_id}")
    def partial_update_booking(self, booking_id, payload: dict, token: str | None = None):
        return self.patch(f"/booking/{booking_id}", json=payload,
                          headers=self._auth_headers(token))

    @allure.step("Delete booking {booking_id}")
    def delete_booking(self, booking_id, token: str | None = None):
        return self.delete(f"/booking/{booking_id}", headers=self._auth_headers(token))
