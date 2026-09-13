from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.ai_agent_service import AIAgentService

router = APIRouter(
    prefix="/api/debug/agent",
    tags=["Agent Debug"],
)


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


@router.post("/chat")
async def agent_chat(payload: AgentChatRequest):
    service = AIAgentService()

    return await service.process(payload.message)