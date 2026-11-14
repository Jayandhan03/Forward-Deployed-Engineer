"""Pagination: offset vs cursor (keyset). Never return an unbounded list.

Offset:  ?limit=10&offset=20   simple, can jump to page N, but slow on big tables (DB scans and skips
                               20 rows) and unstable: rows inserted meanwhile cause duplicates/skips.
Cursor:  ?limit=10&after=<id>  fast (uses an index: WHERE id > :after), stable, but forward-only.
SQL equivalents:  OFFSET 20 LIMIT 10   vs   WHERE id > 30 ORDER BY id LIMIT 10.

Needs: pip install fastapi httpx      Run:  python pagination.py
"""

import base64
import json
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.testclient import TestClient

app = FastAPI()
ROWS = [{"id": i, "name": f"item-{i}"} for i in range(1, 26)]       # 25 rows, ids 1..25
Limit = Annotated[int, Query(ge=1, le=100)]                        # cap it: clients can't ask for 1M rows


@app.get("/offset")
def offset_page(limit: Limit = 10, offset: Annotated[int, Query(ge=0)] = 0):
    items = ROWS[offset: offset + limit]
    return {"items": items, "total": len(ROWS), "limit": limit, "offset": offset}


def encode_cursor(last_id: int) -> str:                            # opaque to clients so you can change it later
    return base64.urlsafe_b64encode(json.dumps({"id": last_id}).encode()).decode()


def decode_cursor(cursor: str) -> int:
    return json.loads(base64.urlsafe_b64decode(cursor))["id"]


@app.get("/cursor")
def cursor_page(limit: Limit = 10, after: str | None = None):
    last_id = decode_cursor(after) if after else 0
    page = [r for r in ROWS if r["id"] > last_id][: limit + 1]      # fetch ONE extra row to know if more exist
    has_more = len(page) > limit
    page = page[:limit]
    return {"items": page, "next_cursor": encode_cursor(page[-1]["id"]) if has_more else None}


if __name__ == "__main__":
    c = TestClient(app)
    print("offset p3:", [r["id"] for r in c.get("/offset?limit=10&offset=20").json()["items"]])
    print("limit=1000 rejected:", c.get("/offset?limit=1000").status_code)

    seen, cursor = [], None
    while True:                                                     # how a client walks every page
        url = "/cursor?limit=10" + (f"&after={cursor}" if cursor else "")
        body = c.get(url).json()
        seen += [r["id"] for r in body["items"]]
        cursor = body["next_cursor"]
        if not cursor:
            break
    print("cursor walk:", seen == list(range(1, 26)), f"({len(seen)} rows, no dupes)")

    print("\nChoose: admin tables / 'page 3 of 8' UI -> offset.  Feeds, infinite scroll, big or changing data -> cursor.")
    print("Cursor sort key must be unique + indexed (id, or (created_at, id)). Offset total = extra COUNT(*) query.")
