from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import anthropic, health, models, openai
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.request_id import RequestIDMiddleware
from app.services.model_registry import ModelRegistry
from app.services.ollama_client import OllamaClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    app.state.settings = settings
    app.state.model_registry = ModelRegistry(settings.model_alias_map)
    app.state.ollama_client = OllamaClient(
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_timeout,
    )
    await app.state.ollama_client.start()

    try:
        yield
    finally:
        await app.state.ollama_client.close()


app = FastAPI(title="Local LLM API Gateway", version="0.1.0", lifespan=lifespan)

app.add_middleware(RequestIDMiddleware)
register_exception_handlers(app)

app.include_router(health.router)
app.include_router(models.router)
app.include_router(openai.router)
app.include_router(anthropic.router)
