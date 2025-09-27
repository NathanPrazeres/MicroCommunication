from fastapi import FastAPI, Response, status

app = FastAPI()

### App ###

@app.get("/rooms")
def get_rooms():
    pass

@app.post("/rooms")
def create_room():
    pass

@app.get("rooms/{room_id}/users")
def get_room_users(room_id: int):
    pass


### Kubernetes ###

@app.get("/healthz")
def get_liveness(response: Response):
    response.status_code = status.HTTP_200_OK
    return "ok"
