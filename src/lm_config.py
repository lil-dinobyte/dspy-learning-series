"""Configuracion de `dspy.LM` desde el entorno.

`dspy` se importa solo al construir el LM, para que importar este modulo no
dispare de inmediato la carga pesada de LiteLLM.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")


def _normalize_ollama_model(model: str) -> str:
    """Prefijo `ollama_chat/` para que LiteLLM use la API de chat."""
    model = model.strip()
    if model.startswith("ollama_chat/") or model.startswith("ollama/"):
        if model.startswith("ollama/") and not model.startswith("ollama_chat/"):
            return "ollama_chat/" + model.removeprefix("ollama/")
        return model
    return f"ollama_chat/{model}"


def _ollama_model_name_for_litellm(model: str | None) -> str:
    """Nombre del modelo sin prefijo `ollama/`, por ejemplo `llama3.2:latest`."""
    raw = (model or os.environ.get("OLLAMA_MODEL") or "llama3.2:latest").strip()
    for prefix in ("ollama_chat/", "ollama/"):
        if raw.startswith(prefix):
            raw = raw.removeprefix(prefix)
            break
    if ":" not in raw:
        raw = f"{raw}:latest"
    return raw


def build_lm_ollama(
    model: str | None = None,
    *,
    api_base: str | None = None,
    **kwargs: Any,
) -> Any:
    """Construye un LM de Ollama via LiteLLM."""
    import dspy

    raw = _ollama_model_name_for_litellm(model)
    model_litellm = _normalize_ollama_model(raw)
    base = (
        api_base or os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434"
    ).rstrip("/")
    return dspy.LM(model_litellm, api_base=base, **kwargs)


def build_lm_openai(model: str | None = None, **kwargs: Any) -> Any:
    import dspy

    model = model or os.environ.get("OPENAI_MODEL", "openai/gpt-4o-mini")
    return dspy.LM(model, **kwargs)


def build_lm_from_env(**kwargs: Any) -> Any:
    """Elige backend segun `DSPY_LM_BACKEND` (`openai` u `ollama`)."""
    backend = (os.environ.get("DSPY_LM_BACKEND") or "openai").strip().lower()
    if backend in ("ollama", "local"):
        return build_lm_ollama(**kwargs)
    if backend != "openai":
        raise ValueError(
            f"DSPY_LM_BACKEND desconocido: {backend!r}. Usa 'openai' u 'ollama'."
        )
    return build_lm_openai(**kwargs)


def configure_lm(lm: Any | None = None, **kwargs: Any) -> Any:
    """Configura el LM por defecto de DSPy y lo devuelve."""
    import dspy

    lm = lm or build_lm_from_env(**kwargs)
    dspy.configure(lm=lm)
    return lm
