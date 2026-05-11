from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.source import Source

router = APIRouter()


@router.get('/', response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(request=request, name='index.html', context={})


@router.get('/sources', response_class=HTMLResponse)
def sources_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    sources = db.execute(select(Source).order_by(Source.created_at.desc())).scalars().all()
    return request.app.state.templates.TemplateResponse(
        request=request, name='sources.html', context={'sources': sources}
    )


@router.get('/sources/{source_id}', response_class=HTMLResponse)
def source_detail_page(source_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    source = db.execute(
        select(Source).options(selectinload(Source.documents).selectinload(Document.chunks)).where(Source.id == source_id)
    ).scalar_one_or_none()
    return request.app.state.templates.TemplateResponse(
        request=request, name='source_detail.html', context={'source': source}
    )


@router.get('/chat', response_class=HTMLResponse)
def chat_page(request: Request, conversation_id: int | None = None, db: Session = Depends(get_db)) -> HTMLResponse:
    conversations = db.execute(select(Conversation).order_by(Conversation.created_at.desc())).scalars().all()
    conversation = None
    if conversation_id:
        conversation = db.execute(
            select(Conversation).options(selectinload(Conversation.messages)).where(Conversation.id == conversation_id)
        ).scalar_one_or_none()
    return request.app.state.templates.TemplateResponse(
        request=request,
        name='chat.html',
        context={
            'conversations': conversations,
            'conversation': conversation,
            'messages': conversation.messages if conversation else [],
            'selected_conversation_id': conversation_id,
        },
    )
