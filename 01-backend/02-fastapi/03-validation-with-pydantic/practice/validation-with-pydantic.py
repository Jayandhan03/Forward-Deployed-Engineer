"""Validation with Pydantic v2: constraints, custom validators, cross-field rules, strictness.

Pydantic is the engine under FastAPI's input AND output. Put rules in the model once and every
endpoint that uses it is protected. Pure pydantic here: no server needed.

Needs: pip install pydantic      Run:  python validation-with-pydantic.py
"""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

Username = Annotated[str, Field(min_length=3, max_length=20, pattern=r"^[a-z0-9_]+$")]   # reusable custom type


class Signup(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)   # reject unknown fields, trim strings

    username: Username
    age: int = Field(ge=13, le=120)
    password: str = Field(min_length=8)
    confirm: str
    role: str = "user"

    @field_validator("role")                       # one field: custom rule
    @classmethod
    def role_allowed(cls, v: str) -> str:
        if v not in {"user", "admin"}:
            raise ValueError("role must be user or admin")
        return v

    @model_validator(mode="after")                 # several fields together
    def passwords_match(self):
        if self.password != self.confirm:
            raise ValueError("passwords do not match")
        return self


def try_it(label: str, data: dict) -> None:
    try:
        m = Signup(**data)
        print(f"{label}: OK -> {m.model_dump(exclude={'password', 'confirm'})}")
    except ValidationError as e:
        print(f"{label}: {e.error_count()} error(s)")
        for err in e.errors():
            print("    ", ".".join(map(str, err["loc"])) or "(model)", "|", err["msg"])


if __name__ == "__main__":
    ok = {"username": "  ana_99 ", "age": "30", "password": "s3cretpass", "confirm": "s3cretpass"}
    try_it("valid (strip + coerce '30')", ok)
    try_it("many problems", {"username": "A!", "age": 5, "password": "short", "confirm": "x", "role": "root"})
    try_it("mismatch", {**ok, "confirm": "nope-nope"})
    try_it("extra field", {**ok, "is_superuser": True})

    print("\nstrict mode (no coercion):")
    try:
        Signup.model_validate({**ok, "age": "30"}, strict=True)
    except ValidationError as e:
        print("    ", e.errors()[0]["loc"], "|", e.errors()[0]["msg"])

    print("\nRules: validate at the edge, once. extra='forbid' catches typos and mass-assignment (is_superuser).")
    print("Constraints (Field) first, @field_validator for one field, @model_validator for cross-field.")
