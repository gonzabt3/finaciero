from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.source import Source, SourceStatus


def retrieve_top_chunks(
    db: Session,
    query_embedding: list[float],
    top_k: int = 5,
    speaker: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[dict]:
    stmt = (
        select(Chunk)
        .join(Chunk.document)
        .join(Document.source)
        .options(selectinload(Chunk.document).selectinload(Document.source))
        .where(Chunk.embedding.is_not(None), Source.status == SourceStatus.processed)
    )
    if speaker:
        # The f-string builds the LIKE pattern value (e.g. '%Milei%') which SQLAlchemy
        # passes as a bind parameter — this is not SQL injection.
        stmt = stmt.where(Chunk.speaker.ilike(f'%{speaker}%'))
    if date_from:
        stmt = stmt.where(Chunk.published_at >= date_from)
    if date_to:
        stmt = stmt.where(Chunk.published_at <= date_to)
    stmt = stmt.order_by(Chunk.embedding.cosine_distance(query_embedding)).limit(top_k)

    chunks = db.execute(stmt).scalars().all()
    return [
        {
            'chunk_id': chunk.id,
            'content': chunk.content,
            'source_id': chunk.document.source.id,
            'source_title': chunk.document.source.title,
            'source_url': chunk.document.source.url,
            'speaker': chunk.speaker,
            'published_at': chunk.published_at,
        }
        for chunk in chunks
    ]


def fallback_recent_chunks(db: Session, top_k: int = 5) -> list[dict]:
    stmt = (
        select(Chunk)
        .join(Chunk.document)
        .join(Document.source)
        .options(selectinload(Chunk.document).selectinload(Document.source))
        .where(Source.status == SourceStatus.processed)
        .order_by(Chunk.created_at.desc())
        .limit(top_k)
    )
    chunks = db.execute(stmt).scalars().all()
    return [
        {
            'chunk_id': chunk.id,
            'content': chunk.content,
            'source_id': chunk.document.source.id,
            'source_title': chunk.document.source.title,
            'source_url': chunk.document.source.url,
            'speaker': chunk.speaker,
            'published_at': chunk.published_at,
        }
        for chunk in chunks
    ]
