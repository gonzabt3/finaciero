from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes import api_sources, chat, ingest, web

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title='Finaciero MVP')
app.state.templates = Jinja2Templates(directory=str(BASE_DIR / 'templates'))
app.mount('/static', StaticFiles(directory=str(BASE_DIR / 'static')), name='static')

app.include_router(web.router)
app.include_router(ingest.router)
app.include_router(chat.router)
app.include_router(api_sources.router)
