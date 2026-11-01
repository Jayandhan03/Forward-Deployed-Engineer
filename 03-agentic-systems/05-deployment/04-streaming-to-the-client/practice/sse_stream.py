"""Streaming to the client with Server-Sent Events, using only the standard library.

The server streams agent events (tokens, tool start/end, done). The client reads them as they
arrive and can cancel mid-run. Runs the server and a demo client in one process.

Run:
    python sse_stream.py
"""

import http.client
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

EVENTS = [
    ("tool_start", {"tool": "lookup_order"}),
    ("tool_end", {"tool": "lookup_order", "ok": True}),
    *[("token", {"text": w + " "}) for w in "Your order shipped yesterday and arrives Friday .".split()],
    ("done", {}),
]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):          # keep the demo output clean
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            for name, data in EVENTS:
                # SSE wire format: "event: x\ndata: {...}\n\n"
                self.wfile.write(f"event: {name}\ndata: {json.dumps(data)}\n\n".encode())
                self.wfile.flush()
                time.sleep(0.05)
        except OSError:                       # BrokenPipe / ConnectionReset / ConnectionAborted (Windows)
            print("   server: client disconnected -> stop the run, stop spending tokens")


def read_events(resp):
    event = None
    for raw in resp:
        line = raw.decode().rstrip("\n")
        if line.startswith("event: "):
            event = line[7:]
        elif line.startswith("data: "):
            yield event, json.loads(line[6:])


def client(cancel_after: int | None = None):
    conn = http.client.HTTPConnection("127.0.0.1", 8765)
    conn.request("GET", "/run")
    text, seen = "", 0
    for event, data in read_events(conn.getresponse()):
        seen += 1
        if event == "token":
            text += data["text"]
            print(f"   client got token: {data['text']!r}")
        elif event.startswith("tool"):
            print(f"   client got {event}: {data['tool']}")
        if event == "done":
            break
        if cancel_after and seen >= cancel_after:
            print("   client: user hit Cancel, closing connection")
            break
    conn.close()
    return text.strip()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    print("full run:")
    print("   final text:", client())
    print("\ncancelled run:")
    client(cancel_after=4)
    time.sleep(0.3)
    server.shutdown()
