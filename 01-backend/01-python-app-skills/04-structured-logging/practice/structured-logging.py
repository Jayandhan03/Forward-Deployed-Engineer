"""Structured logging: one JSON object per line, with a request ID on every line.

Plain-text logs are for humans; JSON logs are searchable ("show me everything for request abc123").
contextvars carry the request ID through any call depth (and across `await`) without passing it
as an argument. Redact secrets in the formatter so no one can forget.

Run:
    python structured-logging.py
"""

import contextvars
import json
import logging
import sys
import uuid

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
SENSITIVE = {"password", "token", "authorization", "api_key"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        extra = getattr(record, "ctx", {})                    # logger.info("x", extra={"ctx": {...}})
        entry.update({k: "***" if k.lower() in SENSITIVE else v for k, v in extra.items()})
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def setup(level: int = logging.INFO) -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)              # stdout: the platform collects it (12-factor)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    return logging.getLogger("app")


log = setup()


def charge(user_id: int, amount: int) -> None:
    log.info("charging", extra={"ctx": {"user_id": user_id, "amount": amount}})  # no request_id passed!
    if amount > 100:
        raise ValueError("limit exceeded")


def handle_request(user_id: int, amount: int) -> None:
    request_id_var.set(uuid.uuid4().hex[:8])                 # middleware sets this once per request
    log.debug("this is hidden at INFO level")
    try:
        charge(user_id, amount)
        log.info("done", extra={"ctx": {"token": "abc-secret-token"}})   # token gets redacted
    except ValueError:
        log.exception("charge failed")                       # ERROR + stack trace, in the same JSON line


if __name__ == "__main__":
    handle_request(1, 50)
    handle_request(2, 500)
    print("\nLevels: DEBUG detail | INFO normal events | WARNING odd but handled | ERROR request failed | CRITICAL down.")
    print("Prod runs at INFO. Log events + IDs, never passwords/tokens/PII. Use structlog for the same idea with less code.")
