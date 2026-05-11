from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.source import Source, SourceStatus


def retrieve_top_chunks(db: Session, query_embedding: list[float], top_k: int = 5) -> list[dict]:
    stmt = (
        select(Chunk)
        .join(Chunk.document)
        .join(Document.source)
        .options(selectinload(Chunk.document).selectinload(Document.source))
        .where(Chunk.embedding.is_not(None), Source.status == SourceStatus.processed)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
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
        }
        for chunk in chunks
    ]
