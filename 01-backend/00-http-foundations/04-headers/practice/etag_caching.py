"""Headers in action: conditional requests with ETag / If-None-Match and Cache-Control.

The server tags each representation with an ETag. The client sends it back in If-None-Match; if
nothing changed the server replies 304 with NO body. Bandwidth saved, response still always correct.

Run:
    python etag_caching.py
"""

import hashlib
import json

resource = {"id": 7, "name": "Acme plan", "price": 49}


def etag_for(body: bytes) -> str:
    return '"' + hashlib.sha256(body).hexdigest()[:16] + '"'


def handle_get(request_headers: dict) -> tuple[int, dict, bytes]:
    body = json.dumps(resource, sort_keys=True).encode()
    tag = etag_for(body)
    headers = {"ETag": tag, "Cache-Control": "private, max-age=0, must-revalidate",
               "Content-Type": "application/json"}
    if request_headers.get("If-None-Match") == tag:
        return 304, headers, b""                              # nothing changed, send no body
    return 200, headers, body


def handle_put(request_headers: dict, new_value: dict) -> tuple[int, dict]:
    """If-Match prevents the lost update: refuse to overwrite a version the client never saw."""
    current = etag_for(json.dumps(resource, sort_keys=True).encode())
    if request_headers.get("If-Match") != current:
        return 412, {"error": "resource changed since you read it, refetch and retry"}
    resource.update(new_value)
    return 200, {"ok": True}


if __name__ == "__main__":
    status, headers, body = handle_get({})
    print(f"1st GET: {status}, {len(body)} bytes, ETag={headers['ETag']}")
    tag = headers["ETag"]

    status, _, body = handle_get({"If-None-Match": tag})
    print(f"2nd GET with If-None-Match: {status}, {len(body)} bytes  <- cache still valid")

    print("\nanother client updates the resource...")
    handle_put({"If-Match": tag}, {"price": 59})

    status, headers, body = handle_get({"If-None-Match": tag})
    print(f"3rd GET with the OLD tag: {status}, {len(body)} bytes, new ETag={headers['ETag']}")

    print("\nlost-update protection:")
    print("  PUT with stale If-Match ->", handle_put({"If-Match": tag}, {"price": 1})[0], "(412 Precondition Failed)")

    print("\nCache-Control cheat sheet: public/private (who may cache), max-age (how long), no-store (never,")
    print("for secrets), must-revalidate (check with ETag before reuse). Auth'd responses: private or no-store.")
