from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from lifespan import lifespan
from config import FRONTEND_SERVICE, FRONTEND_PORT
from api.health import health_router
from api.v1.chat import chat_router
from prometheus_fastapi_instrumentator import Instrumentator
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{FRONTEND_SERVICE}", f"http://localhost:{FRONTEND_PORT}"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

logger.info("Configuring Prometheus instrumentation")
Instrumentator(
    should_instrument_requests_inprogress=True,
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
).instrument(app).expose(app)

app.include_router(health_router)
app.include_router(chat_router)

logger.info("Chat service initialized")
