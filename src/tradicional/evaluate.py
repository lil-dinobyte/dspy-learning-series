
import csv
import json
import subprocess
import sys
from pathlib import Path

from main import (
    MODEL,
    analyze_incident,
    load_prompt,
    IncidentAnalysis,
)


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "exports"
PROMPTS_DIR = EXPORT_DIR / "prompts"
DATASET_PATH = BASE_DIR / "evaluation.json"

PROMPT_VERSIONS = [
    BASE_DIR / "prompt.yaml",
    BASE_DIR / "prompt2.yaml",
]


# ==========================================
# 2. EXPORT RENDERED PROMPT
# ==========================================

def export_prompt(
    incident: dict,
    prompt_path: Path,
) -> None:
    version = prompt_path.stem
    incident_id = incident["id"]

    messages, temperature = load_prompt(
        incident=incident,
        prompt_path=prompt_path,
    )

    output_dir = PROMPTS_DIR / version
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{incident_id}.json"

    request_data = {
        "incident_id": incident_id,
        "prompt_version": version,
        "model": MODEL,
        "temperature": temperature,
        "messages": messages,
        "response_schema": IncidentAnalysis.model_json_schema(),
    }

    output_path.write_text(
        json.dumps(
            request_data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ==========================================
# 3. EVALUATE PROMPT
# ==========================================

def evaluate_prompt(
    prompt_path: Path,
    incidents: list[dict],
) -> dict:
    version = prompt_path.stem
    results = []

    print(f"\n===== {version.upper()} =====")

    for incident in incidents:
        incident_id = incident["id"]

        try:
            # Save the rendered prompt before calling OpenAI.
            export_prompt(incident, prompt_path)

            analysis, usage, latency, _ = analyze_incident(
                incident=incident,
                prompt_path=prompt_path,
            )

            expected = incident["expected_severity"]
            predicted = analysis.severity.value
            correct = predicted == expected

            row = {
                "incident_id": incident_id,
                "prompt_version": version,
                "expected_severity": expected,
                "predicted_severity": predicted,
                "correct": correct,
                "category": analysis.category.value,
                "confidence_score": analysis.confidence_score,
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
                "latency": round(latency, 3),
                "error": None,
            }

            print(
                f"{incident_id} | "
                f"Expected: {expected:<8} | "
                f"Predicted: {predicted:<8} | "
                f"{'PASS' if correct else 'FAIL'}"
            )

        except Exception as exc:
            print(f"{incident_id} | ERROR: {exc}")

            row = {
                "incident_id": incident_id,
                "prompt_version": version,
                "expected_severity": incident["expected_severity"],
                "predicted_severity": None,
                "correct": False,
                "category": None,
                "confidence_score": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "latency": 0,
                "error": str(exc),
            }

        results.append(row)

    # ==========================================
    # 4. SUMMARY
    # ==========================================

    successful = [
        row for row in results
        if row["error"] is None
    ]

    correct_count = sum(
        row["correct"] for row in successful
    )

    accuracy = (
        correct_count / len(successful)
        if successful else 0.0
    )

    summary = {
        "version": version,
        "total_incidents": len(incidents),
        "successful_requests": len(successful),
        "failed_requests": len(incidents) - len(successful),
        "correct_predictions": correct_count,
        "accuracy": round(accuracy, 4),
        "total_tokens": sum(
            row["total_tokens"] for row in results
        ),
        "average_tokens": round(
            sum(row["total_tokens"] for row in successful)
            / len(successful),
            2,
        ) if successful else 0,
        "average_latency": round(
            sum(row["latency"] for row in successful)
            / len(successful),
            3,
        ) if successful else 0,
    }

    print("\nSUMMARY")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    return {
        "summary": summary,
        "results": results,
    }


# ==========================================
# 5. EXPORT EVALUATION
# ==========================================

def export_evaluations(evaluations: list[dict]) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = EXPORT_DIR / "traditional_evaluation.json"
    csv_path = EXPORT_DIR / "traditional_evaluation.csv"

    json_path.write_text(
        json.dumps(
            evaluations,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    rows = [
        row
        for evaluation in evaluations
        for row in evaluation["results"]
    ]

    if rows:
        with csv_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(rows[0].keys()),
            )
            writer.writeheader()
            writer.writerows(rows)

    print(f"\nJSON exported to: {json_path}")
    if rows:
        print(f"CSV exported to: {csv_path}")


# ==========================================
# 6. UPDATE MARKDOWN REPORT
# ==========================================

def update_report() -> None:
    report_script = BASE_DIR / "generate_report.py"

    subprocess.run(
        [sys.executable, str(report_script)],
        check=True,
    )


# ==========================================
# 7. MAIN
# ==========================================

def main() -> None:
    incidents = json.loads(
        DATASET_PATH.read_text(encoding="utf-8")
    )

    evaluations = [
        evaluate_prompt(prompt_path, incidents)
        for prompt_path in PROMPT_VERSIONS
    ]

    export_evaluations(evaluations)

    print("\n========== FINAL COMPARISON ==========")

    for evaluation in evaluations:
        summary = evaluation["summary"]

        print(
            f"{summary['version']}: "
            f"Accuracy={summary['accuracy']:.2%} | "
            f"Avg tokens={summary['average_tokens']} | "
            f"Avg latency={summary['average_latency']}s"
        )

    update_report()

    print("\nEvaluation and Markdown report completed.")


if __name__ == "__main__":
    main()
