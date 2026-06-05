from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class IngestTextRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    text: str = Field(..., min_length=1)
    author: str | None = None
    source_name: str | None = None
    speaker: str | None = None
    published_at: datetime | None = None


class IngestURLRequest(BaseModel):
    url: HttpUrl
    title: str | None = None
