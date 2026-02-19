# Chat API with WebSocket

This project is a simple chat application built using FastAPI and WebSockets, allowing real-time communication between clients.

## Features
- Real-time messaging using WebSockets.
- Basic health check endpoint to verify the server status.

## API Endpoints
- **WebSocket /ws** - Connect to the WebSocket endpoint for real-time chat messages.
- **GET /health** - Check the health of the server.

---

```text markpact:deps python
fastapi
uvicorn[standard]
```

```python markpact:file path=app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

app = FastAPI()

class Message(BaseModel):
    content: str

active_connections: list[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = Message(content=data)
            for connection in active_connections:
                if connection != websocket:
                    await connection.send_text(message.content)
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

```bash markpact:run
uvicorn app.main:app --host 0.0.0.0 --port ${MARKPACT_PORT:-8000}
```

```text markpact:test http
# Health check
GET /health EXPECT 200

# Test WebSocket connection (requires manual testing or additional tools)
WEBSOCKET /ws EXPECT CONNECTED
```