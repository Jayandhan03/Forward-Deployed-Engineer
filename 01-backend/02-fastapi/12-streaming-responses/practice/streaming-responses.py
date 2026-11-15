"""Streaming responses: send data as it is produced (SSE), the backbone of every LLM chat UI.

SSE (Server-Sent Events) = one long-lived HTTP response, content-type text/event-stream, where each
message is `data: <text>\n\n`. One-way (server -> client), auto-reconnect built into browsers'
EventSource, works through normal proxies. A fake "LLM" generator stands in for the model here.

Needs: pip install fastapi httpx      Run:  python streaming-responses.py
"""

import asyncio
import json
import time

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

app = FastAPI()


async def fake_llm(prompt: str):
    for word in f"You asked: {prompt}. Here is a streamed answer.".split():
        await asyncio.sleep(0.05)                      # model latency per token
        yield word + " "


def sse(event: str | None, data: dict | str) -> str:
    payload = data if isinstance(data, str) else json.dumps(data)
    return (f"event: {event}\n" if event else "") + f"data: {payload}\n\n"   # blank line ends the message


@app.get("/chat")
async def chat(prompt: str, request: Request):
    async def events():
        try:
            async for token in fake_llm(prompt):
                if await request.is_disconnected():    # user closed the tab: stop paying for tokens
                    return
                yield sse(None, {"token": token})
            yield sse("done", {"finish_reason": "stop"})
        except Exception:
            yield sse("error", {"message": "generation failed"})   # errors mid-stream can't change the 200 status

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},   # tell nginx not to buffer the stream
    )


@app.get("/plain-stream")                               # chunked streaming without SSE framing (e.g. big file/CSV)
def plain():
    def gen():
        for i in range(3):
            yield f"line {i}\n"
    return StreamingResponse(gen(), media_type="text/plain")


if __name__ == "__main__":
    async def show_timing():                           # what a real client sees: tokens arrive one by one
        start = time.perf_counter()
        async for token in fake_llm("hi"):
            print(f"  +{time.perf_counter() - start:.2f}s  {sse(None, {'token': token})!r}")

    print("token arrival times (generator direct; TestClient buffers the full body so can't show this):")
    asyncio.run(show_timing())

    c = TestClient(app)
    with c.stream("GET", "/chat", params={"prompt": "hi"}) as r:
        print("\nHTTP view -> status:", r.status_code, "|", r.headers["content-type"])
        print("last message:", [ln for ln in r.iter_lines() if ln][-2:])
    print("plain:", c.get("/plain-stream").text.split())

    print("\nWhy: first token in ~50ms instead of waiting for the whole answer. Browser: new EventSource(url)")
    print("(GET only) or fetch() + ReadableStream for POST bodies. Gotchas: proxy buffering (disable it), status is")
    print("already 200 once streaming starts so send an `error` event, and always stop work on client disconnect.")
