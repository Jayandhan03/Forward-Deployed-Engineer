"""Dependency & env management: know which Python and which package versions are really running.

Reproducible builds = pinned versions + a lockfile + one virtualenv per project. This script shows
how to check what is actually installed against what you pinned (what `uv sync --frozen` enforces).

Run:
    python env_check.py
"""

import sys
from importlib import metadata

# Pretend this is your lockfile (uv.lock / poetry.lock / requirements.txt with ==).
LOCKED = {"fastapi": "0.139.0", "pydantic": "2.13.4", "redis": "5.0.0"}
# Pretend this is what `pip freeze` sees in the current env (swap for the real thing: see check()).
FAKE_INSTALLED = {"fastapi": "0.139.0", "pydantic": "2.9.0"}      # pydantic drifted, redis missing


def in_virtualenv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def check(locked: dict[str, str], installed: dict[str, str] | None = None) -> list[str]:
    """installed=None means ask the real environment via importlib.metadata."""
    problems = []
    for name, want in locked.items():
        try:
            have = installed[name] if installed is not None else metadata.version(name)
        except (KeyError, metadata.PackageNotFoundError):
            problems.append(f"{name}: MISSING (want {want})")
            continue
        if have != want:
            problems.append(f"{name}: drift (want {want}, have {have})")
    return problems


if __name__ == "__main__":
    print("python:", sys.version.split()[0], "| in virtualenv:", in_virtualenv())
    problems = check(LOCKED, FAKE_INSTALLED)
    print("lock check:", "OK" if not problems else "FAILED")
    for p in problems:
        print("  -", p)

    print("""
Commands to remember (uv):
  uv init / uv add fastapi          create project / add dep (writes pyproject.toml + uv.lock)
  uv add --dev pytest ruff          dev-only deps, not shipped to prod
  uv sync --frozen                  install EXACTLY the lockfile (CI + Docker); fails on drift
  uv lock --upgrade-package x       bump one dependency deliberately, review the diff
  echo 3.12 > .python-version       pin the interpreter too
Docker: copy pyproject+lock first, install, THEN copy code, so the dep layer is cached.""")
