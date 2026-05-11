from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.source import Source, SourceStatus, SourceType
from app.schemas.ingest import IngestTextRequest
from app.services.chunking import split_into_chunks
from app.services.embeddings import EmbeddingService
from app.services.text_cleaner import clean_text


settings = get_settings()


def ingest_text_source(db: Session, payload: IngestTextRequest) -> Source:
    source = Source(
        type=SourceType.text,
        title=payload.title,
        author=payload.author,
        source_name=payload.source_name,
        status=SourceStatus.pending,
    )
    db.add(source)
    db.flush()

    try:
        cleaned = clean_text(payload.text)
        document = Document(source_id=source.id, raw_text=payload.text, clean_text=cleaned)
        db.add(document)
        db.flush()

        embedding_service = EmbeddingService()
        chunks = split_into_chunks(cleaned, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)
        for chunk in chunks:
            db.add(
                Chunk(
                    document_id=document.id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    embedding=embedding_service.generate_embedding(chunk.content),
                )
            )

        source.status = SourceStatus.processed
        db.commit()
        db.refresh(source)
        return source
    except Exception as exc:
        source.status = SourceStatus.failed
        source.error_message = f'processing_error: {exc.__class__.__name__}'
        db.commit()
        db.refresh(source)
        return source
