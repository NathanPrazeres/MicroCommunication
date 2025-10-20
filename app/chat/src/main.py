from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from lifespan import lifespan
from config import FRONTEND_SERVICE, FRONTEND_PORT
from api.health import health_router
from api.v1.chat import chat_router

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{FRONTEND_SERVICE}", f"http://localhost:{FRONTEND_PORT}"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health_router)
app.include_router(chat_router)
