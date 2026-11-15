"""WebSockets: a persistent two-way connection (chat rooms, live collaboration, voice agents).

HTTP = client asks, server answers, done. WebSocket = after one upgrade handshake, either side can
send any time. A ConnectionManager tracks who's connected so you can broadcast. State lives in
process memory, so with >1 server instance you need Redis pub/sub to fan messages out (05-redis).

Needs: pip install fastapi httpx      Run:  python websockets.py
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, room: str, ws: WebSocket):
        await ws.accept()                                   # complete the handshake
        self.rooms.setdefault(room, []).append(ws)

    def disconnect(self, room: str, ws: WebSocket):
        self.rooms[room].remove(ws)

    async def broadcast(self, room: str, message: dict):
        for ws in list(self.rooms.get(room, [])):
            await ws.send_json(message)


manager = ConnectionManager()


@app.websocket("/ws/{room}")
async def chat(ws: WebSocket, room: str, name: str = "anon", token: str = ""):
    if token != "secret":                                   # auth BEFORE accept (browsers can't set headers: use query/cookie)
        await ws.close(code=1008)                           # 1008 = policy violation
        return
    await manager.connect(room, ws)
    await manager.broadcast(room, {"system": f"{name} joined"})
    try:
        while True:
            text = await ws.receive_text()                  # waits for the next client message
            await manager.broadcast(room, {"from": name, "text": text})
    except WebSocketDisconnect:                             # client left: clean up or you leak connections
        manager.disconnect(room, ws)
        await manager.broadcast(room, {"system": f"{name} left"})


if __name__ == "__main__":
    c = TestClient(app)
    with c.websocket_connect("/ws/general?name=ana&token=secret") as ana:
        print("ana sees:", ana.receive_json())
        with c.websocket_connect("/ws/general?name=bo&token=secret") as bo:
            print("ana sees:", ana.receive_json())          # server pushed this without ana asking
            print("bo sees :", bo.receive_json())
            bo.send_text("hello ana")
            print("ana sees:", ana.receive_json())
            print("bo sees :", bo.receive_json())
        print("ana sees:", ana.receive_json())
    try:
        with c.websocket_connect("/ws/general?name=eve&token=wrong"):
            pass
    except Exception as e:
        print("bad token rejected:", type(e).__name__)

    print("\nPick: SSE for server->client streams (LLM tokens). WebSocket when the client also sends continuously")
    print("(chat, multiplayer, voice/realtime agents). Needs heartbeats (ping), reconnect logic and sticky routing/Redis at scale.")
