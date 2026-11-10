# dspy-lab

Laboratorio para aprender [DSPy](https://dspy.ai/) usando el dominio de contratos de
alquiler como hilo conductor.

A largo plazo el destino es un agente de revisión de contratos. Hoy el foco es el
lab: notebooks, signatures y configuración del LLM. **No brinda asesoramiento
legal.**

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- `OPENAI_API_KEY` en `.env` (recomendado), u [Ollama](https://ollama.com/) en el host si preferís modelo local

## Arranque rápido

1. Copia la configuración de entorno:

```sh
cp .env.example .env
```

Completá `OPENAI_API_KEY` en `.env`.

2. **Local (recomendado):**

```sh
uv sync
```

3. **Opcional — Dev Container** (solo entorno Python; sin Ollama en Docker):

   Abrí la carpeta y ejecutá **Dev Containers: Reopen in Container**.
   La API key se lee desde tu `.env` del host vía Compose.

## Configuración del LLM

Variables principales (ver [`.env.example`](.env.example)):

| Variable | Descripción |
|----------|-------------|
| `DSPY_LM_BACKEND` | `openai` (default) u `ollama` |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Backend OpenAI vía LiteLLM |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | Solo si `DSPY_LM_BACKEND=ollama` y Ollama corre en el host (`http://localhost:11434`) |

En los notebooks, el punto de entrada es [`src/lm_config.py`](src/lm_config.py):

```python
from lm_config import configure_lm

configure_lm()  # lee DSPY_LM_BACKEND y el resto desde .env
```

## Estructura

```text
src/
├── lm_config.py           # Config DSPy desde .env
└── getting_started.ipynb  # Notebook guiado del lab
docs/                      # Roadmap y notas de arquitectura futura
```

## Cómo trabajar

1. Abrí [`src/getting_started.ipynb`](src/getting_started.ipynb).
2. Asegurate de que el LM esté configurado (`configure_lm`) antes de ejecutar predicciones.

### Smoke check con Compose (opcional)

```sh
docker compose up --build -d
docker compose exec app python -c "import dspy; print(dspy.__version__)"
```

## Calidad de código

Instala los hooks de pre-commit (una vez por clon):

```sh
uv run pre-commit install
```

En cada commit se ejecutan formato (Ruff), lint, mypy y pytest (cuando existan tests).

Para correr manualmente sobre todo el repo:

```sh
uv run pre-commit run --all-files
```

Comandos individuales:

```sh
uv run ruff check src
uv run ruff format src
uv run mypy
uv run pytest -v
```

## Docs relacionadas

Material de visión / roadmap (no es la guía operativa del lab):

- [docs/roadmap_m1.md](docs/roadmap_m1.md) — roadmap del Milestone 1
- [docs/workflow.md](docs/workflow.md) — flujo previsto del agente
- [docs/getting_started.md](docs/getting_started.md) — notas de arranque orientadas al producto
