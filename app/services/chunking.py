from dataclasses import dataclass


@dataclass
class ChunkPayload:
    index: int
    content: str
    token_count: int


def _token_count(text: str) -> int:
    return len(text.split())


def split_into_chunks(text: str, chunk_size: int = 900, overlap: int = 150) -> list[ChunkPayload]:
    if chunk_size <= 0:
        raise ValueError('chunk_size must be greater than 0')
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError('overlap must be >= 0 and smaller than chunk_size')

    words = text.split()
    if not words:
        return []

    chunks: list[ChunkPayload] = []
    start = 0
    chunk_index = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        content = ' '.join(words[start:end])
        chunks.append(ChunkPayload(index=chunk_index, content=content, token_count=_token_count(content)))
        if end >= len(words):
            break
        start = max(end - overlap, 0)
        chunk_index += 1

    return chunks
