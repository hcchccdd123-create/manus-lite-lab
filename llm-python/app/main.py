from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.health import router as health_router
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path('data').mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title='Manus Lite Chat Backend', version='0.1.0', lifespan=lifespan)
    app.include_router(health_router, prefix='/api/v1')
    app.include_router(conversations_router, prefix='/api/v1')
    app.include_router(chat_router, prefix='/api/v1')
    return app


app = create_app()
