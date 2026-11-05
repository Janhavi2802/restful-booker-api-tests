# Restful-Booker API Test Automation Framework

![API Tests](https://github.com/Janhavi2802/restful-booker-api-tests/actions/workflows/api-tests.yml/badge.svg)

A Pytest framework for the [Restful-Booker](https://restful-booker.herokuapp.com/apidoc/index.html)
REST API, covering authentication, booking CRUD, data-driven tests, JSON schema
validation and negative/security scenarios. It runs on every push in GitHub
Actions and publishes an Allure report.

## Highlights

- **Reusable API client layer**: one `BaseClient` (session, headers, timeouts,
  logging, Allure attachments) with `AuthClient` and `BookingClient` on top.
  Tests never call `requests` directly.
- **Fixtures** in `conftest.py`: a session-scoped auth token, and a function-scoped
  booking that is created before a test and deleted after it.
- **Per-environment config** in `config/config.yaml`, selected with `--env` and
  overridable with environment variables for CI secrets.
- **Data-driven tests** with `@pytest.mark.parametrize` and JSON data sets in `data/`
  (boundary price 0, same-day check-in/out, Unicode names).
- **JSON schema validation** with `jsonschema` for every response type.
- **Negative coverage**: invalid/missing/injection tokens on PUT, PATCH and DELETE (403),
  bad credentials, missing required fields (4xx/5xx), unknown IDs (404), double delete.
- **Offline mock server** (`mock_server/`) that mirrors the real API's behaviour,
  so the suite runs without internet and gives repeatable results.
- **CI/CD**: GitHub Actions runs against both the mock and the live API on every push,
  nightly, and on demand, in parallel with `pytest-xdist`, then publishes Allure to GitHub Pages.
- **SoapUI** version of the key scenarios, described in [`soapui/`](soapui/README.md).

## Project structure

```
api/
  base_client.py       HTTP layer: session, logging, Allure attachments
  clients.py           AuthClient and BookingClient
  config.py            Loads config/config.yaml per environment
  data_factory.py      Random valid bookings + JSON data loader
  schema_validator.py  jsonschema helper
config/config.yaml     prod and local environments
data/                  Data sets for data-driven tests
schemas/               JSON schemas for responses
mock_server/server.py  Offline mock of Restful-Booker
tests/
  conftest.py          Fixtures and --env option
  test_health.py       Ping / availability
  test_auth.py         Token creation, invalid credentials
  test_booking_crud.py Create, read, filter, update, patch, delete
  test_booking_negative.py  403/404/4xx/5xx paths
soapui/                SoapUI test plan
.github/workflows/     CI pipeline
```

## Running the tests

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

pytest                             # live API (prod)
pytest --env=local                 # offline mock, starts automatically
pytest -m smoke                    # smoke suite only
pytest -m "negative"               # negative suite only
pytest -n auto                     # run in parallel
```

### Allure report

```bash
pytest --env=local
allure serve allure-results        # needs the Allure CLI installed
```

## Test coverage summary

| Area | Tests | Covers |
| --- | --- | --- |
| Health | 2 | Ping status and response time |
| Auth | 8 | Valid token, schema, unique tokens, 6 invalid credential cases |
| Booking CRUD | 13 | Schema, 5 data-driven creates, get, filter, full and partial update, delete |
| Negative | 20 | 9 token × method combos (403), 4 unknown IDs (404), 5 missing fields, empty body, double delete |
| **Total** | **43** | |

## Defects found in the live API

Documented as tests rather than hidden:

1. `POST /booking` with a missing required field returns **500** instead of **400**.
2. `POST /auth` with bad credentials returns **200** with a `reason` field instead of **401**.
3. A successful `DELETE` returns **201 Created** instead of **200/204**.

## Tech stack

Python, Pytest, Requests, jsonschema, PyYAML, Allure, pytest-xdist, pytest-rerunfailures,
GitHub Actions, SoapUI
