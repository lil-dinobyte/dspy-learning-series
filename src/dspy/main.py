
import json
import time
from enum import Enum

import dspy
import mlflow
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# ==========================================
# CONFIGURATION
# ==========================================

load_dotenv()

mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("dspy-sheila")
mlflow.dspy.autolog()

lm = dspy.LM(
    "openai/gpt-4.1-mini",
    temperature=0.0,
    cache=False,
)

dspy.settings.configure(
    lm=lm,
    track_usage=True,
)


# ==========================================
# PYDANTIC MODELS
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
    action: str = Field(
        description="Recommended action"
    )
    priority: Priority = Field(
        description="Action priority"
    )
    risk: str = Field(
        description="Potential risk"
    )


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
# DSPy SIGNATURE
# ==========================================

class IncidentAnalyzer(dspy.Signature):
    """
    Analyze a production technical incident.

    Classify the incident, determine severity using
    the supplied policy, identify probable root causes,
    compare historical incidents, validate evidence,
    and recommend corrective actions.

    Do not fabricate technical evidence.
    Distinguish confirmed facts from hypotheses.

    ROOT CAUSE ANALYSIS:
    Identify the most probable root cause using logs,
    system context, deployments, and historical incidents.

    Do not confuse correlation with causation.

    When a root cause is not directly confirmed,
    describe it as a hypothesis rather than a fact.

    CONFIDENCE ASSESSMENT:
    Estimate confidence in the proposed root cause
    based on the quality of available evidence.

    - 0.90 - 1.00: Root cause directly confirmed
      through logs, metrics, or reproducible tests.

    - 0.70 - 0.89: Strong supporting evidence,
      but the root cause is not fully confirmed.

    - 0.40 - 0.69: Plausible hypothesis supported
      by indirect or incomplete evidence.

    - 0.00 - 0.39: Insufficient or contradictory
      evidence to identify a reliable root cause.

    Do not assign confidence above 0.89 when
    the root cause has not been directly confirmed.

    A historical incident alone is not sufficient
    to confirm the current root cause.

    Missing information must reduce confidence
    when it is essential to validating the hypothesis.
    """

    incident_description: str = dspy.InputField(
        desc="Description of the production incident"
    )

    system_context: str = dspy.InputField(
        desc="Application architecture and infrastructure"
    )

    application_logs: str = dspy.InputField(
        desc="Technical logs related to the incident"
    )

    recent_deployments: str = dspy.InputField(
        desc="Recent changes or deployments"
    )

    historical_incidents: str = dspy.InputField(
        desc="Previous incidents and resolutions"
    )

    business_impact: str = dspy.InputField(
        desc="Impact on customers and business operations"
    )

    severity_policy: str = dspy.InputField(
        desc="Business rules for incident severity"
    )

    category: IncidentCategory = dspy.OutputField(
        desc="Primary incident category"
    )

    severity: Severity = dspy.OutputField(
        desc="Severity according to the provided policy"
    )

    affected_components: list[str] = dspy.OutputField(
        desc="Affected technical components"
    )

    root_cause: str = dspy.OutputField(
        desc="Most probable root cause, identifying uncertainty"
    )

    alternative_causes: list[str] = dspy.OutputField(
        desc="Alternative possible causes"
    )

    supporting_evidence: list[str] = dspy.OutputField(
        desc="Supporting technical evidence"
    )

    missing_information: list[str] = dspy.OutputField(
        desc="Missing evidence or information"
    )

    corrective_actions: list[CorrectiveAction] = dspy.OutputField(
        desc="Recommended actions with priority and risk"
    )

    confidence_score: float = dspy.OutputField(
        desc="Confidence in the proposed root cause, between 0 and 1"
    )

    executive_summary: str = dspy.OutputField(
        desc="Executive summary for non-technical stakeholders"
    )


# ==========================================
# DSPy PREDICTOR
# ==========================================

analyzer = dspy.Predict(IncidentAnalyzer)


# ==========================================
# INCIDENT ANALYSIS
# ==========================================

def analyze_incident(incident: dict) -> IncidentAnalysis:
    result = analyzer(
        incident_description=incident["incident_description"],
        system_context=incident["system_context"],
        application_logs=incident["application_logs"],
        recent_deployments=incident["recent_deployments"],
        historical_incidents=incident["historical_incidents"],
        business_impact=incident["business_impact"],
        severity_policy=incident["severity_policy"],
    )

    return IncidentAnalysis(
        category=result.category,
        severity=result.severity,
        affected_components=result.affected_components,
        root_cause=result.root_cause,
        alternative_causes=result.alternative_causes,
        supporting_evidence=result.supporting_evidence,
        missing_information=result.missing_information,
        corrective_actions=result.corrective_actions,
        confidence_score=result.confidence_score,
        executive_summary=result.executive_summary,
    )


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    incident = {
        "incident_description": (
            "Users are experiencing HTTP 500 errors "
            "when submitting orders after a deployment."
        ),
        "system_context": (
            "FastAPI application using SQLAlchemy and PostgreSQL."
        ),
        "application_logs": (
            "sqlalchemy.exc.TimeoutError: QueuePool limit reached."
        ),
        "recent_deployments": (
            "Version 2.4.1 introduced a background task "
            "that queries the database."
        ),
        "historical_incidents": (
            "A previous incident involved connection pool "
            "exhaustion caused by unclosed sessions."
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

    start = time.perf_counter()

    analysis = analyze_incident(incident)

    latency = time.perf_counter() - start

    # ==========================================
    # STRUCTURED RESULT
    # ==========================================

    print("\n===== DSPy INCIDENT ANALYSIS =====")
    print(
        json.dumps(
            analysis.model_dump(mode="json"),
            indent=2,
            ensure_ascii=False,
        )
    )

    # ==========================================
    # TOKEN USAGE
    # ==========================================

    history = lm.history[-1]
    usage = history.get("usage") or {}

    input_tokens = usage.get(
        "prompt_tokens",
        usage.get("input_tokens", 0),
    )

    output_tokens = usage.get(
        "completion_tokens",
        usage.get("output_tokens", 0),
    )

    total_tokens = usage.get(
        "total_tokens",
        input_tokens + output_tokens,
    )

    print("\n===== TOKEN USAGE =====")
    print(f"Input:  {input_tokens}")
    print(f"Output: {output_tokens}")
    print(f"Total:  {total_tokens}")

    # ==========================================
    # LATENCY
    # ==========================================

    print("\n===== LATENCY =====")
    print(f"{latency:.2f} seconds")

    # ==========================================
    # INSPECT GENERATED PROMPT
    # ==========================================

    print("\n===== DSPy GENERATED PROMPT =====")
    dspy.inspect_history(n=1)




# ==========================================
# 6. HOW TO RUN THE EXPERIMENT
# ==========================================

# 0. Clean old exports (optional)
# rm -rf src/dspy/exports/

# 1. Start MLflow (separate terminal)
# mlflow server --host 0.0.0.0 --port 5000

# 2. Run DSPy baseline (Predict)
# python src/dspy/main.py



# 3. Evaluate all 28 incidents and generate report
# python src/dspy/evaluate.py

# ==========================================
# REPORT GENERATION
# ==========================================

# 4. Regenerate Markdown report from existing JSON
# python src/dspy/generate_report.py
