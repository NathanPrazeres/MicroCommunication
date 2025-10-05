from fastapi import FastAPI
from repositories.db_postgres import postgres_client
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await postgres_client.open()
    yield
    await postgres_client.close()
