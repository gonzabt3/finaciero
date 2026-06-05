from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.source import Source, SourceStatus, SourceType
from app.schemas.ingest import IngestURLRequest
from app.services.article_extractor import extract_article
from app.services.chunking import split_into_chunks
from app.services.embeddings import EmbeddingService
from app.services.text_cleaner import clean_text


settings = get_settings()


def ingest_url_source(db: Session, payload: IngestURLRequest) -> Source:
    source = Source(type=SourceType.article, title=payload.title or str(payload.url), url=str(payload.url), status=SourceStatus.pending)
    db.add(source)
    db.flush()

    try:
        article = extract_article(str(payload.url))
        source.title = payload.title or article['title']
        source.author = article['author']
        source.source_name = article['source_name']
        source.published_at = article['published_at']

        cleaned = clean_text(article['text'])
        document = Document(
            source_id=source.id,
            raw_text=article['text'],
            clean_text=cleaned,
            language=article['language'],
        )
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
                    speaker=source.speaker or source.author,
                    published_at=source.published_at,
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
