
import time
from enum import Enum
from pathlib import Path

import yaml
from dotenv import load_dotenv
from jinja2 import Environment, StrictUndefined
from openai import OpenAI
from pydantic import BaseModel, Field


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

PROMPT_PATH = BASE_DIR / "prompt.yaml"

MODEL = "gpt-4.1-mini"

load_dotenv(BASE_DIR.parent.parent / ".env")

client = OpenAI()


# ==========================================
# 2. ENUMS & RESPONSE MODELS
# ==========================================

class IncidentCategory(str, Enum):
    DATABASE = "Database"
    NETWORK = "Network"
    APPLICATION = "Application"
    INFRASTRUCTURE = "Infrastructure"
    SECURITY = "Security"
    INTEGRATION = "Integration"
    UNKNOWN = "Unknown"


class Severity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Priority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class CorrectiveAction(BaseModel):
    action: str
    priority: Priority
    risk: str


class IncidentAnalysis(BaseModel):
    category: IncidentCategory
    severity: Severity
    affected_components: list[str]
    root_cause: str
    alternative_causes: list[str]
    supporting_evidence: list[str]
    missing_information: list[str]
    corrective_actions: list[CorrectiveAction]
    confidence_score: float = Field(ge=0.0, le=1.0)
    executive_summary: str


# ==========================================
# 3. LOAD & RENDER PROMPT
# ==========================================

def load_prompt(
    incident: dict,
    prompt_path: Path = PROMPT_PATH,
) -> tuple[list[dict], float]:

    config = yaml.safe_load(
        prompt_path.read_text(encoding="utf-8")
    )

    environment = Environment(
        undefined=StrictUndefined,
        autoescape=False,
    )

    messages = [
        {
            "role": message["role"],
            "content": environment.from_string(
                message["content"]
            ).render(**incident),
        }
        for message in config["messages"]
    ]

    temperature = config.get("model", {}).get(
        "temperature", 0.2
    )

    return messages, temperature


# ==========================================
# 4. EXECUTE LLM
# ==========================================

def analyze_incident(
    incident: dict,
    prompt_path: Path = PROMPT_PATH,
):
    messages, temperature = load_prompt(
        incident,
        prompt_path,
    )

    start = time.perf_counter()

    response = client.beta.chat.completions.parse(
        model=MODEL,
        messages=messages,
        response_format=IncidentAnalysis,
        temperature=temperature,
    )

    elapsed = time.perf_counter() - start

    result = response.choices[0].message.parsed

    if result is None:
        raise RuntimeError(
            "OpenAI did not return a valid structured response."
        )

    return result, response.usage, elapsed, messages


# ==========================================
# 5. EXAMPLE INCIDENT
# ==========================================

if __name__ == "__main__":

    incident = {
        "incident_description": (
            "Users are experiencing HTTP 500 errors "
            "when submitting orders after a deployment."
        ),
        "system_context": (
            "FastAPI application using SQLAlchemy "
            "and PostgreSQL."
        ),
        "application_logs": (
            "sqlalchemy.exc.TimeoutError: "
            "QueuePool limit reached."
        ),
        "recent_deployments": (
            "Version 2.4.1 introduced a background "
            "task that queries the database."
        ),
        "historical_incidents": (
            "A previous incident involved connection "
            "pool exhaustion caused by unclosed sessions."
        ),
        "business_impact": (
            "40% of customers cannot complete purchases."
        ),
        "severity_policy": (
            "Critical: complete outage. "
            "High: significant degradation affecting "
            "more than 20% of users."
        ),
    }

    result, usage, elapsed, messages = analyze_incident(
        incident
    )

    # Structured result
    print("\n===== INCIDENT ANALYSIS =====")
    print(result.model_dump_json(indent=2))

    # Token usage
    print("\n===== TOKEN USAGE =====")
    if usage:
        print(f"Input:  {usage.prompt_tokens}")
        print(f"Output: {usage.completion_tokens}")
        print(f"Total:  {usage.total_tokens}")

    # Latency
    print("\n===== LATENCY =====")
    print(f"{elapsed:.2f} seconds")

    # Rendered prompt
    print("\n===== RENDERED PROMPT =====")
    for message in messages:
        print(f"\n--- {message['role'].upper()} ---")
        print(message["content"])

# ==========================================
# 6. EXAMPLE OF HOW TO RUN THE SCRIPT
# ==========================================

# ls -lah src/tradicional/exports/
# rm -rf src/tradicional/exports/
# python src/tradicional/main.py
# python src/tradicional/evaluate.py
# python src/tradicional/generate_report.py
# ls -lah src/tradicional/exports/