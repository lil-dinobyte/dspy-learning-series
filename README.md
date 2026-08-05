# dspy-lab

Laboratorio para aprender [DSPy](https://dspy.ai/) usando el dominio de contratos de
alquiler como hilo conductor.

A largo plazo el destino es un agente de revisión de contratos. Hoy el foco es el
lab: notebooks, signatures y configuración del LLM. **No brinda asesoramiento
legal.**

## Requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker (para Dev Container / Ollama)

## Arranque rápido

1. Copia la configuración de entorno:

```sh
cp .env.example .env
```

2. **Preferido — Dev Container** (Docker + extensión Dev Containers en Cursor/VS Code):

   Abre la carpeta del proyecto y ejecuta **Dev Containers: Reopen in Container**.

   Eso levanta el servicio `app` (Python + DSPy) y `ollama`. Al primer arranque,
   `ollama-init` descarga el modelo definido en `OLLAMA_MODEL`.

3. **Alternativa — local en el host:**

```sh
uv sync
```

Si usas Ollama en el host, en `.env` apunta a:

```env
OLLAMA_BASE_URL=http://localhost:11434
```

## Configuración del LLM

Variables principales (ver [`.env.example`](.env.example)):

| Variable | Descripción |
|----------|-------------|
| `DSPY_LM_BACKEND` | `ollama` (default del lab) u `openai` |
| `OLLAMA_BASE_URL` | `http://ollama:11434` en Compose/Dev Container; `http://localhost:11434` en el host |
| `OLLAMA_MODEL` | Modelo local (p. ej. `llama3.2:latest`) |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Solo si usas el backend OpenAI |

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

### Smoke check con Compose

```sh
docker compose up --build -d
curl http://localhost:11434/api/tags
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
