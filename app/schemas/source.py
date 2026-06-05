from datetime import datetime

from pydantic import BaseModel


class SourceOut(BaseModel):
    id: int
    type: str
    title: str
    author: str | None
    speaker: str | None
    source_name: str | None
    url: str | None
    published_at: datetime | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}
