import json
import logging

from fastapi import APIRouter, Body, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.chat import ChatRequest
from app.services.embeddings import EmbeddingService
from app.services.llm import generate_answer, stream_answer
from app.services.retrieval import fallback_recent_chunks, retrieve_top_chunks

router = APIRouter(tags=['chat'])
logger = logging.getLogger(__name__)


def _is_form_request(request: Request) -> bool:
    content_type = request.headers.get('content-type', '')
    return 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type


def _build_sources(contexts: list[dict]) -> list[dict]:
    return [
        {
            'source_id': item['source_id'],
            'source_title': item['source_title'],
            'source_url': item['source_url'],
            'chunk_id': item['chunk_id'],
        }
        for item in contexts
    ]


def _resolve_contexts(db: Session, question: str, top_k: int) -> list[dict]:
    embedding = EmbeddingService().generate_embedding(question)
    try:
        return retrieve_top_chunks(db, embedding, top_k=top_k)
    except Exception:
        # pgvector extension unavailable or no embeddings yet – fall back to recency ranking
        return fallback_recent_chunks(db, top_k=top_k)


def _get_or_create_conversation(db: Session, conversation_id: int | None, title: str) -> Conversation:
    if conversation_id:
        conversation = db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        ).scalar_one_or_none()
        if conversation:
            return conversation
    conversation = Conversation(title=title[:80])
    db.add(conversation)
    db.flush()
    return conversation


@router.post('/chat')
def chat_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    payload: ChatRequest | None = Body(default=None),
    question: str | None = Form(default=None),
    conversation_id: int | None = Form(default=None),
):
    data = payload or ChatRequest(question=question or '', conversation_id=conversation_id)

    conversation = _get_or_create_conversation(db, data.conversation_id, data.question)
    db.add(Message(conversation_id=conversation.id, role=MessageRole.user, content=data.question))

    contexts = _resolve_contexts(db, data.question, data.top_k)
    answer = generate_answer(data.question, contexts)
    sources = _build_sources(contexts)

    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.assistant,
        content=answer,
        sources_json=sources,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    if _is_form_request(request):
        return RedirectResponse(url=f'/chat?conversation_id={conversation.id}', status_code=303)

    return JSONResponse(
        {
            'answer': answer,
            'conversation_id': conversation.id,
            'assistant_message_id': assistant_message.id,
            'sources': sources,
        }
    )


@router.post('/api/chat/stream')
async def chat_stream_endpoint(
    db: Session = Depends(get_db),
    payload: ChatRequest = Body(...),
):
    """SSE endpoint that streams the assistant answer token by token."""
    conversation = _get_or_create_conversation(db, payload.conversation_id, payload.question)
    db.add(Message(conversation_id=conversation.id, role=MessageRole.user, content=payload.question))
    db.flush()

    contexts = _resolve_contexts(db, payload.question, payload.top_k)
    sources = _build_sources(contexts)
    conversation_id = conversation.id

    async def event_stream():
        accumulated: list[str] = []
        try:
            async for token in stream_answer(payload.question, contexts):
                accumulated.append(token)
                yield f'data: {json.dumps({"type": "token", "content": token})}\n\n'
        except Exception:
            logger.exception('Error while streaming answer for conversation %s', conversation_id)
            yield f'data: {json.dumps({"type": "error", "message": "Error al generar la respuesta."})}\n\n'
            return

        answer = ''.join(accumulated)
        assistant_msg = Message(
            conversation_id=conversation_id,
            role=MessageRole.assistant,
            content=answer,
            sources_json=sources,
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        yield (
            f'data: {json.dumps({"type": "done", "conversation_id": conversation_id, "message_id": assistant_msg.id, "sources": sources})}\n\n'
        )

    return StreamingResponse(
        event_stream(),
        media_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )
