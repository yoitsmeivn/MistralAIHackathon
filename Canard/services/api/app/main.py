# pyright: basic, reportMissingImports=false
from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.analytics import router as analytics_router
from app.routes.callers import router as callers_router
from app.routes.calls import router as calls_router
from app.routes.campaigns import router as campaigns_router
from app.routes.dashboard import router as dashboard_router
from app.routes.employees import router as employees_router
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.scripts import router as scripts_router
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
app.include_router(auth_router)
app.include_router(calls_router)
app.include_router(campaigns_router)
app.include_router(employees_router)
app.include_router(callers_router)
app.include_router(scripts_router)
app.include_router(dashboard_router)
app.include_router(analytics_router)
app.include_router(twilio_router)




if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=True)
