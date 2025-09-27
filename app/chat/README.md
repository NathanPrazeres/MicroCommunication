# Chat Service

## App Endpoints

For simplicity, we'll implement the simplest of endpoints:

### General chatting endpoints

- `GET  /rooms`: lists available rooms
- `POST /rooms`: creates a new room
- `GET  /rooms/{room_id}/users`: lists the users in a room

### Chatting itself

- `GET  /rooms/{room_id}/messages`: fetches recent messages
- `POST /rooms/{room_id}/messages`: sends a message (not in real-time, this is just fallback if WS fails)

### Realtime Chatting

- `WS /ws`: opens a WebSocket connection to the server

## Kubernetes Endpoints

- `GET /healthz`: Kubernetes liveness probe
