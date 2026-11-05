"""JSON schema validation helper."""
import json
from functools import lru_cache
from pathlib import Path

from jsonschema import validate

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"


@lru_cache
def load_schema(name: str) -> dict:
    with open(SCHEMA_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


def assert_schema(instance, schema_name: str) -> None:
    """Raises jsonschema.ValidationError with a clear message if the body is wrong."""
    validate(instance=instance, schema=load_schema(schema_name))
