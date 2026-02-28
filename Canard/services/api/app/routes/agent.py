# pyright: basic, reportMissingImports=false

from fastapi import APIRouter, Response

from app.agents.agent import run_agent_turn
from app.agents.types import AgentConfig
from app.lib.elevenlabs import text_to_speech
from app.lib.sessions import session_store
from app.models import AgentTextRequest, AgentTextResponse, AgentTtsRequest

router = APIRouter(prefix="/api/agent", tags=["agent"])

AGENT_CONFIG = AgentConfig(
    system_prompt="You are Canard, a helpful voice assistant.",
    max_messages=20,
    temperature=0.7,
)


@router.post("/text", response_model=AgentTextResponse)
async def agent_text(req: AgentTextRequest) -> AgentTextResponse:
    sid, state = session_store.get_or_create(req.sessionId)
    result = await run_agent_turn(req.text, state, AGENT_CONFIG)
    session_store.update(sid, result.updated_state)
    return AgentTextResponse(reply=result.output, sessionId=sid)


@router.post("/tts")
async def agent_tts(req: AgentTtsRequest) -> Response:
    audio = await text_to_speech(req.text, req.voiceId)
    return Response(content=audio, media_type="audio/mpeg")
