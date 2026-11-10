"""Configuration & settings: typed, from the environment, validated once at startup.

12-factor: config lives in env vars, not code. pydantic-settings does exactly this in one class
(`class Settings(BaseSettings)`); this stdlib version shows the mechanics so you know what it
buys you: types, defaults, required fields, fail-fast, secrets that don't leak into logs.

Run:
    python configuration-and-settings.py
"""

import os
from dataclasses import dataclass


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Settings:
    env: str
    database_url: str
    port: int
    debug: bool
    api_key: str

    def __repr__(self) -> str:  # secrets never appear in logs or tracebacks
        return f"Settings(env={self.env}, port={self.port}, debug={self.debug}, api_key=***)"


def as_bool(v: str) -> bool:
    return v.strip().lower() in {"1", "true", "yes", "on"}


def load(environ=os.environ) -> Settings:
    errors = []
    for key in ("DATABASE_URL", "API_KEY"):                  # required: no default, must exist
        if not environ.get(key):
            errors.append(f"{key} is required")
    try:
        port = int(environ.get("PORT", "8000"))               # env vars are strings: convert + validate
    except ValueError:
        errors.append("PORT must be an integer")
        port = 0
    env = environ.get("APP_ENV", "dev")
    if env not in {"dev", "staging", "prod"}:
        errors.append("APP_ENV must be dev|staging|prod")
    if errors:                                               # report ALL problems, then crash at boot
        raise ConfigError("; ".join(errors))
    return Settings(env, environ["DATABASE_URL"], port, as_bool(environ.get("DEBUG", "false")), environ["API_KEY"])


if __name__ == "__main__":
    print("1. bad config fails fast, with every problem listed:")
    try:
        load({"PORT": "abc", "APP_ENV": "prod?"})
    except ConfigError as e:
        print("  ", e)

    print("\n2. good config: strings become typed values, defaults apply:")
    s = load({"DATABASE_URL": "postgresql://u:p@db/app", "API_KEY": "sk-secret", "DEBUG": "yes"})
    print("  ", s, "| port type:", type(s.port).__name__)

    print("\nDifferent env = different env vars, SAME code. .env file is for local dev only (git-ignored);")
    print("in prod the platform injects vars. Create Settings once, pass it in; don't read os.environ everywhere.")
