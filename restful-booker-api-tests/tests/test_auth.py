import allure
import pytest

from api.schema_validator import assert_schema


@allure.feature("Auth")
@pytest.mark.smoke
def test_valid_credentials_return_token(auth_client, config):
    response = auth_client.create_token(config.username, config.password)

    assert response.status_code == 200
    assert_schema(response.json(), "auth_token.json")


@allure.feature("Auth")
@pytest.mark.regression
def test_each_login_returns_a_new_token(auth_client, config):
    first = auth_client.create_token(config.username, config.password).json()["token"]
    second = auth_client.create_token(config.username, config.password).json()["token"]
    assert first != second


@allure.feature("Auth")
@pytest.mark.negative
@pytest.mark.parametrize(
    "username, password",
    [
        pytest.param("admin", "wrongpass", id="wrong_password"),
        pytest.param("wronguser", "password123", id="wrong_username"),
        pytest.param("", "", id="empty_credentials"),
        pytest.param("ADMIN", "password123", id="username_case_sensitive"),
        pytest.param("admin' OR '1'='1", "x", id="sql_injection_string"),
        pytest.param("a" * 1000, "b" * 1000, id="very_long_values"),
    ],
)
def test_invalid_credentials_are_rejected(auth_client, username, password):
    response = auth_client.create_token(username, password)

    # Restful-Booker quirk: returns 200 with a reason instead of 401
    assert response.status_code == 200
    body = response.json()
    assert "token" not in body
    assert body.get("reason") == "Bad credentials"
