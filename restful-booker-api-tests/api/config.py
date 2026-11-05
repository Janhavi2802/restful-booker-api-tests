"""Loads per-environment settings from config/config.yaml."""
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "config.yaml"


@dataclass(frozen=True)
class EnvConfig:
    name: str
    base_url: str
    username: str
    password: str
    timeout: int


def load_config(env_name: str | None = None) -> EnvConfig:
    env_name = env_name or os.getenv("API_ENV", "prod")
    with open(CONFIG_FILE, encoding="utf-8") as fh:
        all_envs = yaml.safe_load(fh)

    if env_name not in all_envs:
        raise ValueError(f"Unknown env '{env_name}'. Choose from: {list(all_envs)}")

    env = all_envs[env_name]
    # Secrets can be overridden from CI without editing the file
    return EnvConfig(
        name=env_name,
        base_url=os.getenv("API_BASE_URL", env["base_url"]).rstrip("/"),
        username=os.getenv("API_USERNAME", env["username"]),
        password=os.getenv("API_PASSWORD", env["password"]),
        timeout=int(env.get("timeout", 10)),
    )
