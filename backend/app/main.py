from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ai import generate_world
from .config import get_settings
from .schemas import (
    ErrorResponse,
    WorldCreateRequest,
    WorldRandomRequest,
    WorldResponse,
)

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=dict[str, str])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/world/create", response_model=WorldResponse, responses={502: {"model": ErrorResponse}})
def create_world(payload: WorldCreateRequest) -> WorldResponse:
    result = generate_world(description=payload.description, player_name=payload.player_name)
    return WorldResponse(**result)


@app.post("/api/world/random", response_model=WorldResponse, responses={502: {"model": ErrorResponse}})
def random_world(payload: WorldRandomRequest | None = None) -> WorldResponse:
    player_name = payload.player_name if payload else None
    result = generate_world(description=None, player_name=player_name)
    return WorldResponse(**result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
