# Finaciero MVP

Asistente personal de conocimiento sobre economía con arquitectura monolítica en FastAPI y enfoque MVP-first.

## Stack

- FastAPI + Jinja2 (server-side rendering)
- PostgreSQL + pgvector
- SQLAlchemy 2.0
- Alembic
- OpenAI (opcional, con fallback local)

## Funcionalidades MVP

- Ingesta de texto manual (`POST /ingest/text`)
- Ingesta de artículos por URL (`POST /ingest/url`)
- Listado y detalle de fuentes
- Chat con recuperación de contexto (`POST /chat`)
- Respuestas con trazabilidad de fuentes usadas

## Estructura

```text
app/
  main.py
  config.py
  db.py
  models/
  schemas/
  routes/
  services/
  templates/
  static/
alembic/
alembic.ini
requirements.txt
render.yaml
.env.example
```

## Configuración local

1. Crear entorno virtual e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configurar variables:

```bash
cp .env.example .env
```

3. Ejecutar migraciones:

```bash
alembic upgrade head
```

4. Levantar servidor:

```bash
uvicorn app.main:app --reload
```

Abrir `http://127.0.0.1:8000`.

## Endpoints clave

- Web: `/`, `/sources`, `/sources/{source_id}`, `/chat`
- API: `/api/sources`, `/api/sources/{source_id}`
- Ingesta: `/ingest/text`, `/ingest/url`
- Chat: `/chat`

## Notas y limitaciones del MVP

- No incluye YouTube.
- No incluye autenticación compleja ni multiusuario.
- No usa workers/Celery/Redis.
- Si `OPENAI_API_KEY` no está configurada, embeddings y respuesta de chat usan fallback local para no romper la app.
- El extractor de artículos depende de la calidad del HTML de la URL y puede fallar en sitios bloqueados o anti-bot.
