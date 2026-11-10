"""Evaluate the DSPy Predict baseline on incident severity, tokens and latency."""

import csv
import json
import subprocess
import sys
import time
from pathlib import Path

import dspy
from main import IncidentAnalysis, IncidentAnalyzer, lm


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"
DATASET_PATH = BASE_DIR.parent / "tradicional" / "evaluation.json"

INPUT_FIELDS = (
    "incident_description", "system_context", "application_logs",
    "recent_deployments", "historical_incidents", "business_impact",
    "severity_policy",
)


# ==========================================
# 2. EVALUATE DSPY
# ==========================================

def evaluate_dspy(incidents: list[dict]) -> dict:
    analyzer = dspy.Predict(IncidentAnalyzer)
    results = []

    print("\n===== DSPY BASELINE =====")

    for incident in incidents:
        incident_id = incident["id"]
        expected = incident["expected_severity"]
        inputs = incident.get("inputs", incident)
        inputs = {field: inputs[field] for field in INPUT_FIELDS}

        history_start = len(lm.history)
        start = time.perf_counter()

        try:
            prediction = analyzer(**inputs)
            analysis = IncidentAnalysis.model_validate(dict(prediction))
            predicted = analysis.severity.value
            correct = predicted == expected
            error = None
        except Exception as exc:
            analysis = None
            predicted = None
            correct = False
            error = str(exc)

        latency = round(time.perf_counter() - start, 3)
        usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        for entry in lm.history[history_start:]:
            tokens = entry.get("usage") or {}
            usage["input_tokens"] += tokens.get("prompt_tokens", tokens.get("input_tokens", 0)) or 0
            usage["output_tokens"] += tokens.get("completion_tokens", tokens.get("output_tokens", 0)) or 0
            usage["total_tokens"] += tokens.get("total_tokens") or (
                (tokens.get("prompt_tokens", tokens.get("input_tokens", 0)) or 0)
                + (tokens.get("completion_tokens", tokens.get("output_tokens", 0)) or 0)
            )

        row = {
            "incident_id": incident_id,
            "expected_severity": expected,
            "predicted_severity": predicted,
            "correct": correct,
            "category": analysis.category.value if analysis else None,
            "confidence_score": analysis.confidence_score if analysis else None,
            **usage,
            "latency": latency,
            "error": error,
        }
        results.append(row)

        status = "ERROR" if error else "PASS" if correct else "FAIL"
        print(f"{incident_id} | Expected: {expected:<8} | Predicted: {(predicted or '-'): <8} | {status}")
        if error:
            print(f"  Error: {error}")

    successful = [row for row in results if row["error"] is None]
    correct_count = sum(row["correct"] for row in results)
    summary = {
        "version": "dspy_baseline",
        "total_incidents": len(incidents),
        "successful_requests": len(successful),
        "failed_requests": len(incidents) - len(successful),
        "correct_predictions": correct_count,
        "accuracy": round(correct_count / len(incidents), 4) if incidents else 0.0,
        "total_input_tokens": sum(row["input_tokens"] for row in results),
        "total_output_tokens": sum(row["output_tokens"] for row in results),
        "total_tokens": sum(row["total_tokens"] for row in results),
        "average_tokens": round(sum(row["total_tokens"] for row in successful) / len(successful), 2) if successful else 0,
        "average_latency": round(sum(row["latency"] for row in successful) / len(successful), 3) if successful else 0,
    }

    print("\nSUMMARY")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return {"summary": summary, "results": results}


# ==========================================
# 3. EXPORT EVALUATION
# ==========================================

def export_evaluation(evaluation: dict) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = EXPORT_DIR / "dspy_evaluation.json"
    csv_path = EXPORT_DIR / "dspy_evaluation.csv"

    json_path.write_text(json.dumps([evaluation], indent=2, ensure_ascii=False), encoding="utf-8")

    if evaluation["results"]:
        with csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(evaluation["results"][0].keys()))
            writer.writeheader()
            writer.writerows(evaluation["results"])

    print(f"\nJSON exported to: {json_path}")
    print(f"CSV exported to: {csv_path}")


# ==========================================
# 4. UPDATE MARKDOWN REPORT
# ==========================================

def update_report() -> None:
    subprocess.run([sys.executable, str(BASE_DIR / "generate_report.py")], check=True)


# ==========================================
# 5. MAIN
# ==========================================

def main() -> None:
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    incidents = data if isinstance(data, list) else data["incidents"]

    evaluation = evaluate_dspy(incidents)
    export_evaluation(evaluation)
    update_report()
    print("\nDSPy evaluation and Markdown report completed.")


if __name__ == "__main__":
    main()
