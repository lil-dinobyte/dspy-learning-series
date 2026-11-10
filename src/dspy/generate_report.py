"""Update the DSPy baseline Markdown report from the evaluation JSON."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1] if BASE_DIR.name == 'dspy' else BASE_DIR
EVALUATION_PATH = PROJECT_ROOT / 'src' / 'dspy' / 'exports' / 'dspy_evaluation.json'
REPORT_PATH = PROJECT_ROOT / 'docs' / 'dspy_baseline.md'
START_MARKER = '<!-- RESULTS_START -->'
END_MARKER = '<!-- RESULTS_END -->'


def generate_report() -> None:
    evaluations = json.loads(EVALUATION_PATH.read_text(encoding='utf-8'))
    if isinstance(evaluations, dict):
        evaluations = evaluations.get('evaluations', [evaluations])
    evaluation = evaluations[0]
    summary = evaluation.get('summary', evaluation)
    results = evaluation['results']

    lines = [
        '## Evaluation Results', '',
        '### Summary', '',
        '| Metric | Value |', '|---|---:|',
        f"| Severity accuracy | {summary['accuracy']:.2%} |",
    ]
    metrics = [
        ('Total incidents', 'total_incidents'),
        ('Successful requests', 'successful_requests'),
        ('Failed requests', 'failed_requests'),
        ('Correct predictions', 'correct_predictions'),
        ('Total tokens', 'total_tokens'),
        ('Average tokens', 'average_tokens'),
        ('Average latency (s)', 'average_latency'),
    ]
    for label, key in metrics:
        if key in summary:
            lines.append(f"| {label} | {summary[key]} |")

    lines += [
        '', '### Per-incident results', '',
        '| Incident | Expected | Predicted | Correct | Category | Confidence | Tokens | Latency (s) |',
        '|---|---|---|---|---|---:|---:|---:|',
    ]
    for result in results:
        values = [
            result.get('incident_id'),
            result.get('expected_severity'),
            result.get('predicted_severity'),
            'PASS' if result.get('correct') else 'FAIL',
            result.get('category'),
            result.get('confidence_score'),
            result.get('total_tokens'),
            result.get('latency'),
        ]
        cells = [str(value if value is not None else '—').replace('|', '\\|').replace('\n', ' ') for value in values]
        lines.append('| ' + ' | '.join(cells) + ' |')

    errors = [result for result in results if result.get('error')]
    if errors:
        lines += ['', '### Errors', '']
        for result in errors:
            lines.append(f"- {result['incident_id']}: {result['error']}")

    lines += ['', '> Accuracy measures severity classification only, not the correctness of root causes or evidence.']
    generated = '\n'.join(lines)

    existing = REPORT_PATH.read_text(encoding='utf-8')
    if START_MARKER not in existing or END_MARKER not in existing:
        raise ValueError('Missing RESULTS markers in the Markdown report')
    before, remainder = existing.split(START_MARKER, 1)
    _, after = remainder.split(END_MARKER, 1)
    REPORT_PATH.write_text(
        before + START_MARKER + '\n\n' + generated + '\n\n' + END_MARKER + after,
        encoding='utf-8',
    )
    print(f'Updated report: {REPORT_PATH}')


if __name__ == '__main__':
    generate_report()
