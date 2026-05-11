import json
from datetime import datetime

import httpx
import trafilatura


def extract_article(url: str) -> dict:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        response = httpx.get(url, timeout=20)
        response.raise_for_status()
        downloaded = response.text

    extracted = trafilatura.extract(downloaded, with_metadata=True, output_format='json')
    if not extracted:
        raise ValueError('No se pudo extraer contenido del artículo')

    payload = json.loads(extracted)
    text = (payload.get('text') or '').strip()
    if not text:
        raise ValueError('No se encontró texto útil en la URL')

    published_at = payload.get('date')
    parsed_date = None
    if published_at:
        try:
            parsed_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        except ValueError:
            parsed_date = None

    return {
        'url': url,
        'title': payload.get('title') or url,
        'author': payload.get('author'),
        'source_name': payload.get('sitename'),
        'published_at': parsed_date,
        'text': text,
        'language': payload.get('language'),
    }
