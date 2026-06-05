from fastapi import APIRouter, Body, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.ingest import IngestTextRequest, IngestURLRequest
from app.services.ingest_text import ingest_text_source
from app.services.ingest_url import ingest_url_source

router = APIRouter(tags=['ingest'])


def _is_form_request(request: Request) -> bool:
    content_type = request.headers.get('content-type', '')
    return 'application/x-www-form-urlencoded' in content_type or 'multipart/form-data' in content_type


def _safe_error_message(source_status: str) -> str | None:
    if source_status == 'failed':
        return 'No se pudo procesar la fuente. Revisa la URL o el contenido e inténtalo nuevamente.'
    return None


@router.post('/ingest/text')
def ingest_text(
    request: Request,
    db: Session = Depends(get_db),
    payload: IngestTextRequest | None = Body(default=None),
    title: str | None = Form(default=None),
    text: str | None = Form(default=None),
    author: str | None = Form(default=None),
    source_name: str | None = Form(default=None),
    speaker: str | None = Form(default=None),
    published_at: str | None = Form(default=None),
):
    if payload is None:
        from datetime import datetime
        parsed_published_at = None
        if published_at:
            try:
                parsed_published_at = datetime.fromisoformat(published_at)
            except ValueError:
                pass
        payload = IngestTextRequest(
            title=title or '',
            text=text or '',
            author=author,
            source_name=source_name,
            speaker=speaker,
            published_at=parsed_published_at,
        )
    source = ingest_text_source(db, payload)

    if _is_form_request(request):
        return RedirectResponse(url=f'/sources/{source.id}', status_code=303)

    return JSONResponse(
        {'source_id': source.id, 'status': source.status.value, 'error_message': _safe_error_message(source.status.value)}
    )


@router.post('/ingest/url')
def ingest_url(
    request: Request,
    db: Session = Depends(get_db),
    payload: IngestURLRequest | None = Body(default=None),
    url: str | None = Form(default=None),
    title: str | None = Form(default=None),
):
    data = payload or IngestURLRequest(url=url or '', title=title)
    source = ingest_url_source(db, data)

    if _is_form_request(request):
        return RedirectResponse(url=f'/sources/{source.id}', status_code=303)

    return JSONResponse(
        {'source_id': source.id, 'status': source.status.value, 'error_message': _safe_error_message(source.status.value)}
    )
