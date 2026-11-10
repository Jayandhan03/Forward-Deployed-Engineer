"""Project layout: routers -> services -> repositories, dependencies point one way only.

On disk this is  src/app/{api,services,repositories,schemas,domain,core}/ . Here the layers are
classes in one file so you can run it. The rule to take away: the router knows HTTP, the service
knows business rules, the repository knows storage. Nobody reaches "up" a layer.

Run:
    python layered_app.py
"""

from dataclasses import dataclass


# --- domain: plain objects + rules, no framework, no DB ------------------------------------------
@dataclass
class User:
    id: int
    email: str


class EmailTaken(Exception):
    pass


# --- repository: the ONLY place that knows how data is stored (swap dict for Postgres) ----------
class UserRepository:
    def __init__(self):
        self._rows: dict[int, User] = {}

    def by_email(self, email: str) -> User | None:
        return next((u for u in self._rows.values() if u.email == email), None)

    def add(self, email: str) -> User:
        user = User(id=len(self._rows) + 1, email=email)
        self._rows[user.id] = user
        return user


# --- service: business rules; takes its repo as an argument (that is the testability trick) ------
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def register(self, email: str) -> User:
        email = email.strip().lower()
        if self.repo.by_email(email):
            raise EmailTaken(email)
        return self.repo.add(email)


# --- router: translates HTTP <-> service calls; no business rules, no storage code ---------------
def post_users(service: UserService, body: dict) -> tuple[int, dict]:
    try:
        user = service.register(body["email"])
        return 201, {"id": user.id, "email": user.email}
    except EmailTaken:
        return 409, {"error": "email already registered"}


if __name__ == "__main__":
    service = UserService(UserRepository())          # composition root: wire layers together once
    print(post_users(service, {"email": "A@x.com"}))
    print(post_users(service, {"email": "a@x.com"}))  # duplicate -> 409, rule lives in the service

    # Testing the service needs no HTTP and no DB: pass a fake repo.
    class FakeRepo(UserRepository):
        pass

    print("service test:", UserService(FakeRepo()).register("t@x.com"))

    print("\nDependency direction:  api -> services -> repositories -> domain.  Never the reverse.")
    print("Where things live: config + logging in core/, tests mirror src/, one place wires it all (main.py).")
