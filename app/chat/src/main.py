from fastapi import FastAPI
from lifespan import lifespan
from api.health import health_router
from api.v1.chat import chat_router

app = FastAPI(lifespan=lifespan)

app.include_router(health_router)
app.include_router(chat_router)
