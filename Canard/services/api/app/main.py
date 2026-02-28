# pyright: basic, reportMissingImports=false
from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.config import settings
from app.routes.callers import router as callers_router
from app.routes.calls import router as calls_router
from app.routes.campaigns import router as campaigns_router
from app.routes.dashboard import router as dashboard_router
from app.routes.employees import router as employees_router
from app.routes.health import router as health_router
from app.routes.scripts import router as scripts_router
from app.services.media import get_audio
from app.twilio_voice.routes import router as twilio_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(
    title="Canard API",
    description="Voice-Based Security Simulation & Resilience Evaluation Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(calls_router)
app.include_router(campaigns_router)
app.include_router(employees_router)
app.include_router(callers_router)
app.include_router(scripts_router)
app.include_router(dashboard_router)
app.include_router(twilio_router)


@app.get("/media/{media_id}")
async def serve_media(media_id: str) -> Response:
    audio = get_audio(media_id)
    if audio is None:
        return Response(content="Not found", status_code=404)
    # audio/basic = mu-law 8 kHz (RFC 2046 §4.3) — the telephony default.
    # ElevenLabs TTS outputs raw ulaw_8000 samples (no file headers).
    # NOTE: Twilio <Play> may not support audio/basic via HTTP; this endpoint
    # is mainly used by the fallback gather flow.  The primary streaming flow
    # sends audio directly over the Media Stream WebSocket.
    return Response(content=audio, media_type="audio/basic")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
