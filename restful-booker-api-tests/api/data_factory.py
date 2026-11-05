"""Builds booking payloads: static data sets from data/ plus randomised fresh data."""
import json
import random
import string
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data(file_name: str):
    with open(DATA_DIR / file_name, encoding="utf-8") as fh:
        return json.load(fh)


def _random_name(prefix: str) -> str:
    return prefix + "".join(random.choices(string.ascii_lowercase, k=5))


def build_booking(**overrides) -> dict:
    """A valid booking with unique names, so parallel runs don't clash."""
    checkin = date.today() + timedelta(days=random.randint(1, 30))
    payload = {
        "firstname": _random_name("Jan"),
        "lastname": _random_name("Test"),
        "totalprice": random.randint(100, 5000),
        "depositpaid": random.choice([True, False]),
        "bookingdates": {
            "checkin": checkin.isoformat(),
            "checkout": (checkin + timedelta(days=random.randint(1, 7))).isoformat(),
        },
        "additionalneeds": random.choice(["Breakfast", "Lunch", "Late checkout"]),
    }
    payload.update(deepcopy(overrides))
    return payload
