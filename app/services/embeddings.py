import hashlib

from openai import OpenAI

from app.config import get_settings


settings = get_settings()


class EmbeddingService:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    def generate_embedding(self, text: str) -> list[float]:
        clean = text.strip()
        if not clean:
            return [0.0] * settings.EMBEDDING_DIM

        if self._client:
            response = self._client.embeddings.create(model=settings.EMBEDDING_MODEL, input=clean)
            return response.data[0].embedding

        digest = hashlib.sha256(clean.encode('utf-8')).digest()
        return [((digest[i % len(digest)] / 255.0) * 2.0) - 1.0 for i in range(settings.EMBEDDING_DIM)]
