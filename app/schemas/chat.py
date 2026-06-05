from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    conversation_id: int | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    speaker: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class ChatSource(BaseModel):
    source_id: int
    source_title: str
    source_url: str | None = None
    chunk_id: int


class ChatResponse(BaseModel):
    answer: str
    conversation_id: int
    assistant_message_id: int
    sources: list[ChatSource]
