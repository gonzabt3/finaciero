from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.source import Source
from app.schemas.source import SourceOut

router = APIRouter(prefix='/api', tags=['sources'])


@router.get('/sources', response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)) -> list[Source]:
    return db.execute(select(Source).order_by(Source.created_at.desc())).scalars().all()


@router.get('/sources/{source_id}', response_model=SourceOut)
def get_source(source_id: int, db: Session = Depends(get_db)) -> Source:
    source = db.execute(select(Source).where(Source.id == source_id)).scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail='Source not found')
    return source
