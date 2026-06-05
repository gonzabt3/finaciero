import asyncio
import logging
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI, OpenAI

from app.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()

_FALLBACK_PREFIX = (
    'Modo fallback activo (sin OPENAI_API_KEY). '
    'Aquí tienes una respuesta basada en el contexto recuperado:\n\n'
)
_NO_SOURCES = 'No encontré fuentes relevantes todavía. Carga más contenido e inténtalo de nuevo.'


def build_prompt(question: str, contexts: list[dict]) -> str:
    context_block = '\n\n'.join([f"[{idx + 1}] {item['content']}" for idx, item in enumerate(contexts)])
    return (
        'Eres un asistente de conocimiento económico. '
        'Responde usando solamente el contexto recuperado cuando sea posible. '
        'Si no alcanza, di claramente qué falta.\n\n'
        f'Contexto:\n{context_block}\n\n'
        f'Pregunta: {question}\n'
        'Respuesta:'
    )


def generate_answer(question: str, contexts: list[dict]) -> str:
    if not contexts:
        return _NO_SOURCES

    prompt = build_prompt(question, contexts)
    if settings.OPENAI_API_KEY:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or 'No se pudo generar una respuesta.'

    return _FALLBACK_PREFIX + contexts[0]['content'][:900]


async def stream_answer(question: str, contexts: list[dict]) -> AsyncGenerator[str, None]:
    """Yield answer tokens one by one; used by the SSE streaming endpoint."""
    if not contexts:
        yield _NO_SOURCES
        return

    prompt = build_prompt(question, contexts)

    if settings.OPENAI_API_KEY:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        stream = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.2,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                yield content
    else:
        fallback_text = _FALLBACK_PREFIX + contexts[0]['content'][:900]
        for word in fallback_text.split(' '):
            yield word + ' '
            await asyncio.sleep(0.02)
