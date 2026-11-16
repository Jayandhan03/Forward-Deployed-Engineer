"""OpenAPI & Swagger: FastAPI turns your code into a machine-readable API contract.

/openapi.json is the contract (OpenAPI 3.1). /docs is Swagger UI and /redoc is ReDoc, both rendered
from it. Customer engineers, frontend codegen (openapi-typescript, orval), Postman and API
gateways all consume this one file. Good metadata = a good contract = fewer support questions.

Needs: pip install fastapi httpx      Run:  python openapi_contract.py
"""

import json
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI(
    title="Invoices API",
    version="1.2.0",
    description="Create and fetch invoices.",
    openapi_tags=[{"name": "invoices", "description": "Invoice operations"}],
    # docs_url=None, redoc_url=None,                      # hide docs in prod if the API is private
)


class InvoiceIn(BaseModel):
    customer: str = Field(description="Customer legal name", examples=["Acme GmbH"])
    amount_cents: int = Field(gt=0, description="Amount in cents, avoids float rounding", examples=[12900])


class InvoiceOut(InvoiceIn):
    id: int


class ErrorOut(BaseModel):
    detail: str


@app.post(
    "/invoices",
    response_model=InvoiceOut,
    status_code=201,
    tags=["invoices"],
    summary="Create an invoice",
    operation_id="createInvoice",                       # becomes the generated client's method name: client.createInvoice()
    responses={409: {"model": ErrorOut, "description": "Duplicate invoice"}},   # document non-200 outcomes too
)
def create_invoice(body: InvoiceIn):
    return {"id": 1, **body.model_dump()}


@app.get("/invoices/{invoice_id}", response_model=InvoiceOut, tags=["invoices"], operation_id="getInvoice",
         responses={404: {"model": ErrorOut}})
def get_invoice(invoice_id: int, expand: bool = Query(False, description="Include line items")):
    raise HTTPException(404, "invoice not found")


if __name__ == "__main__":
    c = TestClient(app)
    spec = c.get("/openapi.json").json()
    print("openapi:", spec["openapi"], "| title:", spec["info"]["title"], "| version:", spec["info"]["version"])
    for path, methods in spec["paths"].items():
        for method, op in methods.items():
            print(f"  {method.upper():5} {path:24} operationId={op['operationId']:14} responses={sorted(op['responses'])}")
    print("schemas:", sorted(spec["components"]["schemas"]))
    print("InvoiceIn.amount_cents:", json.dumps(spec["components"]["schemas"]["InvoiceIn"]["properties"]["amount_cents"]))
    print("docs UI:", c.get("/docs").status_code, "| redoc:", c.get("/redoc").status_code)

    out = Path(tempfile.mkdtemp()) / "openapi.json"     # export the contract: in a real repo commit it and diff it in PRs
    out.write_text(json.dumps(spec, indent=2))
    print("wrote", out)

    print("""
Next steps with the spec:
  TypeScript client : npx openapi-typescript openapi.json -o api.d.ts      (types only)
                      npx orval --input openapi.json                      (full client + React Query hooks)
  Contract testing  : fail CI if the spec changes unexpectedly (diff openapi.json, or use schemathesis to fuzz it).
  Rule              : set operation_id, document error responses, give fields descriptions/examples.""")
