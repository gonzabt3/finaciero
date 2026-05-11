from fastapi import APIRouter, Body, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.chat import ChatRequest
from app.services.embeddings import EmbeddingService
from app.services.llm import generate_answer
from app.services.retrieval import fallback_recent_chunks, retrieve_top_chunks

router = APIRouter(tags=['chat'])


def _is_form_request(request: Request) -> bool:
    content_type = request.headers.get('content-type', '')
    return 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type


@router.post('/chat')
def chat_endpoint(
    request: Request,
    db: Session = Depends(get_db),
    payload: ChatRequest | None = Body(default=None),
    question: str | None = Form(default=None),
    conversation_id: int | None = Form(default=None),
):
    data = payload or ChatRequest(question=question or '', conversation_id=conversation_id)

    conversation = None
    if data.conversation_id:
        conversation = db.execute(select(Conversation).where(Conversation.id == data.conversation_id)).scalar_one_or_none()
    if conversation is None:
        conversation = Conversation(title=data.question[:80])
        db.add(conversation)
        db.flush()

    db.add(Message(conversation_id=conversation.id, role=MessageRole.user, content=data.question))

    embedding = EmbeddingService().generate_embedding(data.question)
    try:
        contexts = retrieve_top_chunks(db, embedding, top_k=data.top_k)
    except Exception:
        contexts = fallback_recent_chunks(db, top_k=data.top_k)

    answer = generate_answer(data.question, contexts)
    sources = [
        {
            'source_id': item['source_id'],
            'source_title': item['source_title'],
            'source_url': item['source_url'],
            'chunk_id': item['chunk_id'],
        }
        for item in contexts
    ]

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
