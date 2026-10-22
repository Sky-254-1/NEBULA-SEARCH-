"""AI answer, streaming, and chat history routes."""

import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.database.repositories.chat import ChatRepository
from app.database.repositories.user import UserRepository
from app.middleware.rate_limit import rate_limit
from app.models.schemas import (
    AIRequest,
    AIResponse,
    ChatHistoryResponse,
    ChatMessage,
    SynthesizeRequest,
    SynthesizeResponse,
)
from app.services.ai import get_ai_answer, stream_ai_answer, synthesize_snippets
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


@router.post("/ask", response_model=AIResponse, dependencies=[Depends(rate_limit)])
async def ai_ask(body: AIRequest, email: str = Depends(get_current_user), db=Depends(get_db)):
    answer, provider = await get_ai_answer(body.prompt)
    if not answer:
        raise HTTPException(
            status_code=404,
            detail="No AI answer available for this query. Try rephrasing.",
        )

    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if user_id:
        chat = ChatRepository(db)
        await chat.add_message(user_id, "user", body.prompt)
        await chat.add_message(user_id, "assistant", answer)

    return AIResponse(answer=answer, provider=provider)


@router.post("/ask/stream", dependencies=[Depends(rate_limit)])
async def ai_ask_stream(body: AIRequest, email: str = Depends(get_current_user)):
    _ = email

    async def event_generator():
        async for chunk in stream_ai_answer(body.prompt):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/chat/history", response_model=ChatHistoryResponse)
async def chat_history(email: str = Depends(get_current_user), db=Depends(get_db)):
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if not user_id:
        return ChatHistoryResponse(messages=[])
    chat = ChatRepository(db)
    rows = await chat.list_for_user(user_id)
    return ChatHistoryResponse(
        messages=[ChatMessage(role=row["role"], content=row["content"]) for row in rows]
    )


@router.delete("/chat/history")
async def clear_chat_history(email: str = Depends(get_current_user), db=Depends(get_db)):
    users = UserRepository(db)
    user_id = await users.get_id_by_email(email)
    if user_id:
        chat = ChatRepository(db)
        await chat.clear_for_user(user_id)
    return {"message": "Chat history cleared"}


@router.post("/synthesize", response_model=SynthesizeResponse, dependencies=[Depends(rate_limit)])
async def synthesize(body: SynthesizeRequest, email: str = Depends(get_current_user)):
    _ = email
    return await synthesize_snippets(body.query, body.snippets)
