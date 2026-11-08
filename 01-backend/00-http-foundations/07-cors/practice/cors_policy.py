"""CORS: a browser rule, enforced by the browser, configured by the server.

For "non-simple" cross-origin requests the browser first sends an OPTIONS preflight. The server's
response headers tell the browser whether to allow the real request. Servers and curl ignore CORS;
only browsers enforce it. It is NOT authentication.

Run:
    python cors_policy.py
"""

ALLOWED_ORIGINS = {"https://app.acme.com", "http://localhost:3000"}
ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE"}
ALLOWED_HEADERS = {"content-type", "authorization"}


def cors_headers(origin: str | None, with_credentials: bool = False) -> dict:
    if origin not in ALLOWED_ORIGINS:
        return {}                                              # no CORS headers -> browser blocks the read
    headers = {
        "Access-Control-Allow-Origin": origin,                 # echo ONE allowed origin, not a wildcard
        "Vary": "Origin",                                      # caches must key on Origin
    }
    if with_credentials:
        headers["Access-Control-Allow-Credentials"] = "true"   # cookies allowed (never combine with *)
    return headers


def handle(method: str, request_headers: dict) -> tuple[int, dict]:
    origin = request_headers.get("Origin")
    if method == "OPTIONS":                                    # preflight
        wanted_method = request_headers.get("Access-Control-Request-Method", "")
        wanted_headers = {h.strip().lower() for h in request_headers.get("Access-Control-Request-Headers", "").split(",") if h}
        if wanted_method not in ALLOWED_METHODS or not wanted_headers <= ALLOWED_HEADERS:
            return 403, {}
        return 204, {**cors_headers(origin, True),
                     "Access-Control-Allow-Methods": ", ".join(sorted(ALLOWED_METHODS)),
                     "Access-Control-Allow-Headers": ", ".join(sorted(ALLOWED_HEADERS)),
                     "Access-Control-Max-Age": "600"}          # let the browser cache the preflight
    return 200, cors_headers(origin, True)


if __name__ == "__main__":
    scenarios = [
        ("allowed origin, simple GET", "GET", {"Origin": "https://app.acme.com"}),
        ("evil origin, GET", "GET", {"Origin": "https://evil.example"}),
        ("preflight for POST + JSON + auth", "OPTIONS", {"Origin": "https://app.acme.com",
            "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type, Authorization"}),
        ("preflight for PATCH (not allowed)", "OPTIONS", {"Origin": "https://app.acme.com",
            "Access-Control-Request-Method": "PATCH", "Access-Control-Request-Headers": "Content-Type"}),
    ]
    for label, method, headers in scenarios:
        status, resp = handle(method, headers)
        allow = resp.get("Access-Control-Allow-Origin", "(none -> browser blocks it)")
        print(f"{label:<36} -> {status}  Allow-Origin: {allow}")

    print("\nRules: never reflect arbitrary Origins with credentials; avoid '*' for authenticated APIs;")
    print("remember CORS only restricts browsers, so the API still needs real authn/authz.")
