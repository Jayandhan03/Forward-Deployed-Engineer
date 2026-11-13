"""Exception handlers: turn domain errors into consistent HTTP error responses, in one place.

Handlers raise meaningful errors (`OrderNotFound`); registered handlers map them to status + JSON.
Also override FastAPI's built-in 422 and 500 so EVERY error has the same shape:
    {"error": {"code": "...", "message": "...", "request_id"?: ...}}

Needs: pip install fastapi httpx      Run:  python exception-handlers.py
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

app = FastAPI()


class DomainError(Exception):
    status = 400
    code = "domain_error"

    def __init__(self, message: str):
        self.message = message


class OrderNotFound(DomainError):
    status, code = 404, "order_not_found"


class PaymentDeclined(DomainError):
    status, code = 402, "payment_declined"


def err(status: int, code: str, message: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, **extra}})


@app.exception_handler(DomainError)                      # covers every subclass
async def domain_handler(request: Request, exc: DomainError):
    return err(exc.status, exc.code, exc.message)


@app.exception_handler(RequestValidationError)           # override the default 422 shape
async def validation_handler(request: Request, exc: RequestValidationError):
    fields = [{"field": ".".join(map(str, e["loc"][1:])), "problem": e["msg"]} for e in exc.errors()]
    return err(422, "validation_error", "Invalid request", fields=fields)


@app.exception_handler(HTTPException)                    # keep HTTPException consistent too
async def http_handler(request: Request, exc: HTTPException):
    return err(exc.status_code, "http_error", str(exc.detail))


@app.exception_handler(Exception)                        # last resort: never leak a traceback
async def unhandled(request: Request, exc: Exception):
    print(f"  [log] UNHANDLED {type(exc).__name__}: {exc}")           # real detail goes to logs only
    return err(500, "internal_error", "Something went wrong")


@app.get("/orders/{oid}")
def get_order(oid: int):
    if oid == 0:
        raise OrderNotFound(f"order {oid} does not exist")
    if oid == 13:
        raise PaymentDeclined("card declined")
    if oid == 500:
        raise RuntimeError("db password is hunter2")                  # must NOT reach the client
    if oid == 401:
        raise HTTPException(401, "login required")
    return {"id": oid}


if __name__ == "__main__":
    c = TestClient(app, raise_server_exceptions=False)               # let the 500 handler answer, like prod
    for path in ("/orders/1", "/orders/0", "/orders/13", "/orders/401", "/orders/abc", "/orders/500"):
        r = c.get(path)
        print(r.status_code, r.json())
    print("\nRule: business code raises domain errors, knows no HTTP. Handlers own status codes + the error shape.")
    print("One error shape for the whole API = clients write one parser. Never return str(exc) for unknown errors.")
