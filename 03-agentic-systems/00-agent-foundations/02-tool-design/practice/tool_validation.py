"""Tool design: strict schema, validate before running, return errors the model can act on.

Run:
    python tool_validation.py
"""

TOOL_SCHEMA = {
    "name": "create_ticket",
    # Description is written FOR the model: when to use it, when not to, what comes back.
    "description": "Create a support ticket. Use only after search_tickets found no duplicate. "
                   "Returns the new ticket id.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "maxLength": 80},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            "assignee": {"type": "string"},
        },
        "required": ["title", "priority"],
        "additionalProperties": False,
    },
}

TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool}


def validate(args: dict, schema: dict) -> list[str]:
    """Tiny JSON-schema subset. In real code use the `jsonschema` package."""
    errors = []
    props = schema["properties"]
    for name in schema.get("required", []):
        if name not in args:
            errors.append(f"missing required field '{name}'")
    for name, value in args.items():
        if name not in props:
            errors.append(f"unknown field '{name}' (allowed: {', '.join(props)})")
            continue
        p = props[name]
        # bool is a subclass of int in Python, so True would otherwise pass as an integer
        if not isinstance(value, TYPES[p["type"]]) or (isinstance(value, bool) and p["type"] != "boolean"):
            errors.append(f"'{name}' must be {p['type']}, got {type(value).__name__}")
        elif "enum" in p and value not in p["enum"]:
            errors.append(f"'{name}' must be one of {p['enum']}, got '{value}'")
        elif "maxLength" in p and len(value) > p["maxLength"]:
            errors.append(f"'{name}' too long ({len(value)} > {p['maxLength']})")
    return errors


def create_ticket(title: str, priority: str, assignee: str | None = None) -> str:
    return "TCK-1042"


def execute(args: dict) -> dict:
    """Never raise into the agent loop. Return a tool_result the model can read and fix."""
    errors = validate(args, TOOL_SCHEMA["input_schema"])
    if errors:
        return {"is_error": True, "content": "Invalid input: " + "; ".join(errors)}
    return {"is_error": False, "content": create_ticket(**args)}


if __name__ == "__main__":
    for args in [
        {"title": "Login broken", "priority": "high"},
        {"title": "Login broken", "priority": "urgent"},
        {"priority": "low", "colour": "red"},
        {"title": 123, "priority": "low"},
        {"title": True, "priority": "low"},
    ]:
        print(args, "\n  ->", execute(args))
