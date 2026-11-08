"""JSON and serialization pitfalls: what json.dumps can't do, and how to do it deliberately.

JSON has strings, numbers, booleans, null, arrays, objects. Everything else (dates, decimals,
sets, bytes, your classes) needs an explicit, documented encoding.

Run:
    python json_pitfalls.py
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass
class Invoice:
    id: int
    total: Decimal
    issued: datetime
    tags: set[str]


def default(obj):
    """One place that defines how non-JSON types are written."""
    if isinstance(obj, datetime):
        return obj.astimezone(timezone.utc).isoformat()         # ISO 8601, always UTC
    if isinstance(obj, Decimal):
        return str(obj)                                         # string: no float rounding for money
    if isinstance(obj, set):
        return sorted(obj)                                      # deterministic order
    raise TypeError(f"{type(obj).__name__} is not serialisable")


if __name__ == "__main__":
    inv = Invoice(7, Decimal("19.99"), datetime(2026, 11, 8, 9, 30, tzinfo=timezone.utc), {"b", "a"})

    print("1. naive dumps fails on real types:")
    try:
        json.dumps(asdict(inv))
    except TypeError as e:
        print("  ", e)

    print("\n2. explicit encoding:")
    text = json.dumps(asdict(inv), default=default)
    print("  ", text)

    print("\n3. floats lie about money:")
    print("   0.1 + 0.2 =", 0.1 + 0.2, "| Decimal('0.1') + Decimal('0.2') =", Decimal("0.1") + Decimal("0.2"))

    print("\n4. big integers lose precision in JavaScript clients (numbers are 64-bit floats):")
    big = 2**53 + 1
    print(f"   server id {big} -> JS reads it as {float(big):.0f}; send large ids as strings")

    print("\n5. parsing is not validating:")
    payload = json.loads('{"id": "7", "total": "abc"}')
    print("  ", payload, "-> types are whatever the sender chose; validate with a schema (Pydantic) at the boundary")

    print("\n6. NaN/Infinity are not valid JSON:", end=" ")
    try:
        json.dumps({"x": float("nan")}, allow_nan=False)
    except ValueError as e:
        print("rejected ->", e)
