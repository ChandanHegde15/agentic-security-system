#!/usr/bin/env python3
"""Read-only audit of saved Agent 4 benchmark predictions.

This script does not edit the frozen benchmark, predictions, or metrics. Rows
whose expected label is null are counted separately and excluded from exact
case-match denominators because there is no expected object to compare against.
Recorded row errors are reported independently from whether a parsed prediction
exists; this avoids automatically treating a harness exception as a model
inference failure.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "models/agent4_recovered_adapters/external_benchmark/external_benchmark_predictions.json"


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main() -> int:
    if not PREDICTIONS.is_file():
        raise SystemExit(f"Prediction artifact not found: {PREDICTIONS}")
    rows = json.loads(PREDICTIONS.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit("Expected prediction artifact to contain a JSON array")

    scored: list[dict[str, Any]] = []
    null_expected: list[dict[str, Any]] = []
    parseable = 0
    recorded_errors = 0
    package_action_matches = 0
    package_action_comparisons = 0

    for row in rows:
        if not isinstance(row, dict):
            continue
        if row.get("prediction_parsed") is not None:
            parseable += 1
        if row.get("error"):
            recorded_errors += 1
        expected = row.get("expected")
        if expected is None:
            null_expected.append(row)
            continue
        predicted = row.get("prediction_parsed")
        scored.append(row)
        if not isinstance(expected, dict) or not isinstance(predicted, dict):
            continue
        expected_recs = expected.get("recommendations")
        predicted_recs = predicted.get("recommendations")
        if not isinstance(expected_recs, list) or not isinstance(predicted_recs, list):
            continue
        by_name = {x.get("package_name"): x for x in predicted_recs if isinstance(x, dict)}
        for exp in expected_recs:
            if not isinstance(exp, dict):
                continue
            pred = by_name.get(exp.get("package_name"))
            if pred is None:
                continue
            package_action_comparisons += 1
            if exp.get("action") == pred.get("action"):
                package_action_matches += 1

    exact_matches = sum(
        1 for row in scored
        if row.get("prediction_parsed") is not None
        and canonical(row.get("expected")) == canonical(row.get("prediction_parsed"))
    )
    output = {
        "source_file": str(PREDICTIONS.relative_to(ROOT)),
        "rows": len(rows),
        "rows_with_parsed_prediction": parseable,
        "rows_with_recorded_error_field": recorded_errors,
        "scorable_rows_non_null_expected": len(scored),
        "null_expected_rows_excluded_from_exact_match": len(null_expected),
        "null_expected_case_ids": [r.get("case_id") for r in null_expected],
        "exact_case_matches_full_object": exact_matches,
        "exact_case_match_rate_on_scorable_rows": exact_matches / len(scored) if scored else None,
        "package_action_matches": package_action_matches,
        "package_action_comparisons": package_action_comparisons,
        "package_action_accuracy": package_action_matches / package_action_comparisons if package_action_comparisons else None,
        "warning": "Read-only audit of saved records. Does not re-run inference or establish whether recorded row errors originated in model generation or evaluator code.",
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
