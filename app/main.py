import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth, exports, items, lists
from app.core.config import settings
from app.core.errors import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    os.makedirs(settings.export_dir, exist_ok=True)
    yield


app = FastAPI(title="Swibit Learning Tracker", version="0.1.0", lifespan=lifespan)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(lists.router)
app.include_router(items.router)
app.include_router(exports.router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
