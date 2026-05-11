from openai import OpenAI

from app.config import get_settings


settings = get_settings()


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
        return 'No encontré fuentes relevantes todavía. Carga más contenido e inténtalo de nuevo.'

    prompt = build_prompt(question, contexts)
    if settings.OPENAI_API_KEY:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or 'No se pudo generar una respuesta.'

    return (
        'Modo fallback activo (sin OPENAI_API_KEY). '
        'Aquí tienes una respuesta basada en el contexto recuperado:\n\n'
        + contexts[0]['content'][:900]
    )
