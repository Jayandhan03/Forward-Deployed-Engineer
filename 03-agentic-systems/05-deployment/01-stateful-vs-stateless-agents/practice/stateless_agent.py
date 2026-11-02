"""Stateful vs stateless: where does the conversation live?

Stateful server: history lives in this process's memory. Fast, but restart or a second instance
loses it, and you can't scale out without sticky sessions.

Stateless server: history lives in a shared store keyed by session id. Any instance can serve any
request, so you can scale out, restart freely, and resume.

Run:
    python stateless_agent.py
"""


def fake_agent(history: list[str], user_msg: str) -> str:
    return f"(turn {len(history) // 2 + 1}) you said: {user_msg!r}; I remember {len(history)} earlier messages"


class StatefulServer:
    def __init__(self):
        self.history: list[str] = []               # state trapped inside this instance

    def handle(self, session: str, msg: str) -> str:
        reply = fake_agent(self.history, msg)
        self.history += [msg, reply]
        return reply


SHARED_STORE: dict[str, list[str]] = {}            # stands in for Redis / Postgres


class StatelessServer:
    def handle(self, session: str, msg: str) -> str:
        history = SHARED_STORE.get(session, [])    # load
        reply = fake_agent(history, msg)
        SHARED_STORE[session] = history + [msg, reply]   # save
        return reply


if __name__ == "__main__":
    print("STATEFUL, two instances behind a load balancer:")
    a, b = StatefulServer(), StatefulServer()
    print("  A:", a.handle("s1", "hi"))
    print("  A:", a.handle("s1", "what's my order status?"))
    print("  B:", b.handle("s1", "and the refund?"), " <- landed on B, context is gone")

    print("\nSTATELESS, same two instances:")
    a, b = StatelessServer(), StatelessServer()
    print("  A:", a.handle("s2", "hi"))
    print("  A:", a.handle("s2", "what's my order status?"))
    print("  B:", b.handle("s2", "and the refund?"), " <- B reads the shared store, context intact")

    print("\nRule: keep the process stateless, keep the state in a store. Long runs: store checkpoints too.")
