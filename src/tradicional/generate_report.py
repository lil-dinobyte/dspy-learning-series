
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RESULTS_PATH = (
    ROOT / "src" / "tradicional" / "exports"
    / "traditional_evaluation.json"
)

DOC_PATH = ROOT / "docs" / "traditional_prompt_engineering.md"

START_MARKER = "<!-- RESULTS_START -->"
END_MARKER = "<!-- RESULTS_END -->"


def format_number(value: int | float, decimals: int = 0) -> str:
    """Format numbers using Spanish notation."""
    return (
        f"{value:,.{decimals}f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def generate_table(evaluations: list[dict]) -> str:
    versions = [item["summary"]["version"] for item in evaluations]

    lines = [
        "| Métrica | " + " | ".join(
            f"`{version}.yaml`" for version in versions
        ) + " |",
        "|---|" + "---:|" * len(versions),
    ]

    metrics = [
        ("Incidentes evaluados", "total_incidents", lambda v: str(v)),
        ("Solicitudes exitosas", "successful_requests", str),
        ("Solicitudes fallidas", "failed_requests", str),
        ("Predicciones correctas", "correct_predictions", str),
        ("Accuracy", "accuracy", lambda v: f"{format_number(v * 100, 1)}%"),
        ("Tokens totales", "total_tokens", format_number),
        ("Tokens promedio", "average_tokens", lambda v: format_number(v, 2)),
        ("Latencia promedio", "average_latency", lambda v: f"{format_number(v, 3)} s"),
    ]

    for label, key, formatter in metrics:
        values = [
            formatter(item["summary"][key])
            for item in evaluations
        ]
        lines.append(f"| {label} | " + " | ".join(values) + " |")

    return "\n".join(lines)


def generate_errors_table(evaluations: list[dict]) -> str:
    errors = []

    for evaluation in evaluations:
        version = evaluation["summary"]["version"]

        for result in evaluation["results"]:
            if not result["correct"]:
                errors.append(
                    f"| {version}.yaml "
                    f"| {result['incident_id']} "
                    f"| {result['expected_severity']} "
                    f"| {result['predicted_severity']} |"
                )

    if not errors:
        return "No se detectaron clasificaciones incorrectas."

    return "\n".join([
        "| Versión | Incidente | Esperado | Predicho |",
        "|---|---|---|---|",
        *errors,
    ])


def main() -> None:
    evaluations = json.loads(
        RESULTS_PATH.read_text(encoding="utf-8")
    )

    report = "\n".join([
        "#### Resultados de la evaluación",
        "",
        generate_table(evaluations),
        "",
        "#### Clasificaciones incorrectas",
        "",
        generate_errors_table(evaluations),
    ])

    document = DOC_PATH.read_text(encoding="utf-8")

    if document.count(START_MARKER) != 1 or document.count(END_MARKER) != 1:
        raise ValueError(
            "El Markdown debe contener exactamente un par "
            "de marcadores RESULTS_START y RESULTS_END."
        )

    start = document.index(START_MARKER) + len(START_MARKER)
    end = document.index(END_MARKER)

    if end < start:
        raise ValueError("Los marcadores están en el orden incorrecto.")

    updated = (
        document[:start]
        + "\n\n"
        + report
        + "\n\n"
        + document[end:]
    )

    DOC_PATH.write_text(updated, encoding="utf-8")
    print(f"Reporte actualizado: {DOC_PATH}")


if __name__ == "__main__":
    main()
