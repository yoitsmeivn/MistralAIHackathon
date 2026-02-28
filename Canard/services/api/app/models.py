# pyright: basic, reportMissingImports=false

from pydantic import BaseModel


class AgentTextRequest(BaseModel):
    sessionId: str | None = None
    text: str
    model_config = {"populate_by_name": True}


class AgentTextResponse(BaseModel):
    reply: str
    sessionId: str
    model_config = {"populate_by_name": True}


class AgentTtsRequest(BaseModel):
    text: str
    voiceId: str | None = None
    model_config = {"populate_by_name": True}


class HealthResponse(BaseModel):
    status: str
    timestamp: str
