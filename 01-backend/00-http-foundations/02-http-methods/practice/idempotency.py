"""HTTP methods: safe vs idempotent, and the Idempotency-Key pattern that makes POST retry-safe.

  GET     safe (no side effects), idempotent
  PUT     idempotent: sending it twice leaves the same state as once
  DELETE  idempotent
  POST    NOT idempotent: a retry can create a duplicate (double charge, double order)

Networks time out, clients retry. If a retry can double-charge someone, that is a bug.

Run:
    python idempotency.py
"""

import uuid

orders: dict[str, dict] = {}
idempotency_cache: dict[str, dict] = {}       # key -> the response we already gave


def post_order_naive(body: dict) -> dict:
    order_id = uuid.uuid4().hex[:6]
    orders[order_id] = body
    return {"status": 201, "id": order_id}


def post_order_idempotent(body: dict, idempotency_key: str) -> dict:
    if idempotency_key in idempotency_cache:                   # replay: same answer, no new side effect
        return {**idempotency_cache[idempotency_key], "replayed": True}
    response = post_order_naive(body)
    idempotency_cache[idempotency_key] = response
    return response


def put_order(order_id: str, body: dict) -> dict:
    orders[order_id] = body                                    # "set to this", repeatable
    return {"status": 200, "id": order_id}


if __name__ == "__main__":
    print("naive POST, client retries after a timeout:")
    for _ in range(2):
        post_order_naive({"item": "laptop", "qty": 1})
    print(f"  orders created: {len(orders)}  <- the customer is charged twice\n")

    orders.clear()
    print("POST with Idempotency-Key, same retry:")
    key = "client-generated-uuid-123"
    for attempt in (1, 2, 3):
        print(f"  attempt {attempt}:", post_order_idempotent({"item": "laptop", "qty": 1}, key))
    print(f"  orders created: {len(orders)}\n")

    orders.clear()
    print("PUT twice:")
    put_order("o1", {"item": "laptop", "qty": 1})
    put_order("o1", {"item": "laptop", "qty": 1})
    print(f"  orders: {len(orders)} (same end state)")

    print("\nIn production: store the key with the request hash, expire after ~24h, and reject the same key")
    print("used with a different body. Payment APIs and any 'create' endpoint called by agents or queues need this.")
