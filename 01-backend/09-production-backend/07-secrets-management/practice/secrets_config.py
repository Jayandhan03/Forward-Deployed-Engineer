"""Secrets management: config from the environment, fail fast, never log secrets.

Secrets never live in code or git. They come from the environment (or a secret manager that
injects them). Validate at startup so a missing secret crashes the deploy, not a user request.

Run:
    python secrets_config.py
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    api_key: str
    debug: bool = False

    def __repr__(self) -> str:                      # logging the settings must not leak secrets
        return f"Settings(database_url={mask(self.database_url)}, api_key={mask(self.api_key)}, debug={self.debug})"


def mask(value: str) -> str:
    return value[:3] + "***" if len(value) > 6 else "***"


def load_settings(env: dict) -> Settings:
    required = ["DATABASE_URL", "API_KEY"]
    missing = [k for k in required if not env.get(k)]
    if missing:
        raise RuntimeError(f"missing required settings: {', '.join(missing)}")
    return Settings(env["DATABASE_URL"], env["API_KEY"], env.get("DEBUG", "").lower() == "true")


if __name__ == "__main__":
    print("1. missing secret fails at startup:")
    try:
        load_settings({"DATABASE_URL": "postgres://u:p@db/app"})
    except RuntimeError as e:
        print("  ", e)

    print("\n2. loaded settings are safe to log:")
    s = load_settings({"DATABASE_URL": "postgres://user:hunter2@db/app", "API_KEY": "sk-live-abcdef123456"})
    print("  ", s)

    print("\n3. real environment (this process):", "API_KEY" in os.environ and "set" or "not set")

    print("\nRules: .env files stay out of git (.gitignore), rotate secrets on leak, give each environment")
    print("its own secrets, least privilege per key. A secret committed once is compromised forever.")
