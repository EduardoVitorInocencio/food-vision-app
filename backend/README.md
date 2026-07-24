# food-vision-api

API FastAPI para análise estruturada de imagens de alimentos com a OpenAI.

## Execução local

```powershell
Copy-Item .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

Configure `OPENAI_API_KEY` no arquivo `.env`. Nunca versione esse arquivo.

## Endpoints

- `GET /health`
- `POST /api/v1/food-analysis` com o campo multipart `image`

## Qualidade

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```
