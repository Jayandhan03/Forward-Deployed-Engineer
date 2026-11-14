"""File uploads: multipart bodies, size limits, type checks, streaming to disk.

Rules for a safe upload endpoint:
  1. Check the real type (magic bytes), not just the filename or the client's Content-Type.
  2. Enforce a max size WHILE reading (never `await file.read()` a 2 GB body into memory).
  3. Never trust the filename: generate your own (path traversal: "../../etc/passwd").
  4. Store the file in object storage (S3) and keep only the key in your DB.

Needs: pip install fastapi httpx python-multipart      Run:  python file-uploads.py
"""

import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.testclient import TestClient

app = FastAPI()
UPLOAD_DIR = Path(tempfile.mkdtemp(prefix="uploads-"))
MAX_BYTES = 1024                                   # tiny so the demo can hit it; real: 5-20 MB
CHUNK = 256
MAGIC = {b"\x89PNG\r\n\x1a\n": ".png", b"%PDF-": ".pdf", b"\xff\xd8\xff": ".jpg"}


def sniff(head: bytes) -> str | None:
    return next((ext for sig, ext in MAGIC.items() if head.startswith(sig)), None)


@app.post("/upload", status_code=201)
async def upload(file: UploadFile = File(...)):
    head = await file.read(16)                     # 1. look at the first bytes
    ext = sniff(head)
    if ext is None:
        raise HTTPException(415, "only PNG, JPG and PDF allowed")
    await file.seek(0)

    name = f"{uuid.uuid4().hex}{ext}"              # 3. our name, never file.filename
    size = 0
    with open(UPLOAD_DIR / name, "wb") as out:
        while chunk := await file.read(CHUNK):     # 2. stream in chunks, count as we go
            size += len(chunk)
            if size > MAX_BYTES:
                out.close()
                (UPLOAD_DIR / name).unlink()
                raise HTTPException(413, f"file too large (max {MAX_BYTES} bytes)")
            out.write(chunk)
    return {"stored_as": name, "original_name": file.filename, "bytes": size}


@app.post("/multi")
async def multi(files: list[UploadFile]):          # several files in one request
    return {"names": [f.filename for f in files]}


if __name__ == "__main__":
    c = TestClient(app)
    png = b"\x89PNG\r\n\x1a\n" + b"x" * 100
    r = c.post("/upload", files={"file": ("../../evil.png", png, "image/png")})
    print(r.status_code, r.json(), "<- hostile filename ignored")
    r = c.post("/upload", files={"file": ("virus.png", b"MZ\x90\x00 not an image", "image/png")})
    print(r.status_code, r.json(), "<- lying Content-Type/extension caught by magic bytes")
    r = c.post("/upload", files={"file": ("big.png", png + b"x" * 5000, "image/png")})
    print(r.status_code, r.json())
    print("files on disk:", len(list(UPLOAD_DIR.iterdir())), "(the rejected big one was deleted)")
    print("multi:", c.post("/multi", files=[("files", ("a.txt", b"1")), ("files", ("b.txt", b"2"))]).json())

    print("\nBig files / production: let the client upload straight to S3 via a presigned URL (07-file-storage),")
    print("and set a body-size limit at the proxy (nginx client_max_body_size) so bad requests die early.")
