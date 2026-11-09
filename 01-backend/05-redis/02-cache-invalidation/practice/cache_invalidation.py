"""Cache invalidation: cache-aside, TTLs, and the stale-data race.

Cache-aside: read the cache, on a miss read the DB and fill the cache. On writes, update the DB
then DELETE the cache key (don't update it: deleting is simpler and avoids write-order races).
A TTL is the safety net that bounds how long any mistake can live.

Run:
    python cache_invalidation.py
"""

import time

DB = {"user:1": {"name": "Alice", "plan": "free"}}
CACHE: dict[str, tuple[float, dict]] = {}     # key -> (expires_at, value)
STATS = {"hits": 0, "misses": 0, "db_reads": 0}


def get(key: str, ttl_s: float = 60.0) -> dict:
    entry = CACHE.get(key)
    if entry and entry[0] > time.time():
        STATS["hits"] += 1
        return entry[1]
    STATS["misses"] += 1
    STATS["db_reads"] += 1
    value = dict(DB[key])
    CACHE[key] = (time.time() + ttl_s, value)
    return value


def update_buggy(key: str, **changes) -> None:
    """Forgets to invalidate: readers see stale data until the TTL expires."""
    DB[key].update(changes)


def update(key: str, **changes) -> None:
    """DB first, then delete the cache key. The next read refills it with fresh data."""
    DB[key].update(changes)
    CACHE.pop(key, None)


if __name__ == "__main__":
    print("1. cache-aside:")
    get("user:1"); get("user:1"); get("user:1")
    print("  ", STATS, "-> 1 DB read serves 3 requests")

    print("\n2. write without invalidation (bug):")
    update_buggy("user:1", plan="pro")
    print("   DB says  :", DB["user:1"]["plan"])
    print("   cache says:", get("user:1")["plan"], "<- stale until TTL expires")

    print("\n3. write with invalidation:")
    update("user:1", plan="enterprise")
    print("   cache says:", get("user:1")["plan"], "<- fresh")

    print("\n4. TTL as a safety net:")
    update_buggy("user:1", plan="free")
    CACHE["user:1"] = (time.time() + 0.05, CACHE["user:1"][1])    # pretend a short TTL
    print("   before expiry:", get("user:1")["plan"])
    time.sleep(0.06)
    print("   after expiry :", get("user:1")["plan"], "<- bounded staleness")

    print("\nRules: invalidate on write, always set a TTL, expect races (add jitter to TTLs to avoid")
    print("a thundering herd when many keys expire together).")
