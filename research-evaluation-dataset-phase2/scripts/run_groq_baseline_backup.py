import json
import os
import sys
import time
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path.cwd()
DATASET = REPO_ROOT / "research-evaluation-dataset-phase2" / "research_evaluation_dataset.json"
OUT_DIR = REPO_ROOT / "research-evaluation-dataset-phase2" / "baseline_results"

sys.path.insert(0, str(REPO_ROOT))

from agents.pipeline import run_pipeline
from agents.recommendation.llm.groq_provider import GroqProvider


class StubClient:
    def __init__(self, outcomes):
        self.outcomes = outcomes or {}

    def get_package_metadata(self, package_name):
        if package_name not in self.outcomes:
            return None
        return self.outcomes[package_name]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def make_project(project_dir, case):
    files = case["project_input"]["files"]

    for name, content in files.items():
        path = project_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def normalize_recommendations(result):
    recs = result.get("recommendations", {})
    if isinstance(recs, dict):
        return recs.get("recommendations", [])
    if isinstance(recs, list):
        return recs
    return []


def expected_recommendations(case):
    gt = case.get("agent_4_ground_truth")

    if not gt:
        return []

    if isinstance(gt, dict):
        return gt.get("recommendations", [])

    return []


def compare_recommendations(predicted, expected):
    expected_by_pkg = {
        r.get("package_name"): r
        for r in expected
    }

    predicted_by_pkg = {
        r.get("package_name"): r
        for r in predicted
    }

    package_names = sorted(set(expected_by_pkg) | set(predicted_by_pkg))

    rows = []

    for package in package_names:
        exp = expected_by_pkg.get(package)
        pred = predicted_by_pkg.get(package)

        action_match = (
            exp is not None
            and pred is not None
            and exp.get("action") == pred.get("action")
        )

        suggested_match = (
            exp is not None
            and pred is not None
            and exp.get("suggested_package") == pred.get("suggested_package")
        )

        evidence_expected = set(exp.get("evidence_referenced", [])) if exp else set()
        evidence_predicted = set(pred.get("evidence_referenced", [])) if pred else set()

        evidence_match = (
            exp is not None
            and pred is not None
            and evidence_expected == evidence_predicted
        )

        exact_match = (
            action_match
            and suggested_match
            and evidence_match
        )

        rows.append({
            "package_name": package,
            "expected_action": exp.get("action") if exp else None,
            "predicted_action": pred.get("action") if pred else None,
            "action_match": action_match,
            "expected_suggested_package": exp.get("suggested_package") if exp else None,
            "predicted_suggested_package": pred.get("suggested_package") if pred else None,
            "suggested_package_match": suggested_match,
            "expected_evidence": sorted(evidence_expected),
            "predicted_evidence": sorted(evidence_predicted),
            "evidence_match": evidence_match,
            "exact_match": exact_match,
        })

    return rows


def main():
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not set.")

    if not DATASET.exists():
        raise FileNotFoundError(DATASET)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATASET, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    cases = dataset["cases"]

    dataset_hash = sha256_file(DATASET)

    provider = GroqProvider()

    print("=" * 72)
    print("AGENTIC SECURITY SYSTEM - GROQ BASELINE EVALUATION")
    print("=" * 72)
    print(f"Cases       : {len(cases)}")
    print(f"Model       : {provider.model}")
    print(f"Dataset SHA : {dataset_hash}")
    print("=" * 72)

    all_results = []

    for index, case in enumerate(cases, start=1):
        case_id = case["case_id"]

        print(f"\n[{index:02d}/{len(cases):02d}] {case_id} "
              f"{case['category']}/{case['subcategory']}")

        project_id = case["project_input"]["project_id"]

        with TemporaryDirectory(prefix=f"baseline-{case_id}-") as tmp:
            project_dir = Path(tmp) / project_id
            project_dir.mkdir(parents=True)

            make_project(project_dir, case)

            pypi_client = StubClient(case.get("registry_pypi", {}))
            npm_client = StubClient(case.get("registry_npm", {}))

            started = time.perf_counter()

            try:
                result = run_pipeline(
                    project_dir,
                    llm_provider=provider,
                    pypi_client=pypi_client,
                    npm_client=npm_client,
                )

                elapsed = time.perf_counter() - started

                predicted = normalize_recommendations(result)
                expected = expected_recommendations(case)

                comparison = compare_recommendations(
                    predicted,
                    expected,
                )

                action_correct = sum(
                    1 for x in comparison
                    if x["action_match"]
                )

                exact_correct = sum(
                    1 for x in comparison
                    if x["exact_match"]
                )

                total_packages = len(comparison)

                record = {
                    "case_id": case_id,
                    "project_id": project_id,
                    "category": case["category"],
                    "subcategory": case["subcategory"],
                    "status": "success",
                    "latency_seconds": round(elapsed, 4),
                    "predicted_recommendations": predicted,
                    "expected_recommendations": expected,
                    "package_comparisons": comparison,
                    "action_correct": action_correct,
                    "exact_correct": exact_correct,
                    "total_packages": total_packages,
                    "pipeline_output": result,
                }

                print(
                    f"  SUCCESS | packages={total_packages} "
                    f"| action={action_correct}/{total_packages} "
                    f"| exact={exact_correct}/{total_packages} "
                    f"| {elapsed:.2f}s"
                )

            except Exception as exc:
                elapsed = time.perf_counter() - started

                record = {
                    "case_id": case_id,
                    "project_id": project_id,
                    "category": case["category"],
                    "subcategory": case["subcategory"],
                    "status": "error",
                    "latency_seconds": round(elapsed, 4),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }

                print(
                    f"  ERROR | {type(exc).__name__}: {exc}"
                )

            all_results.append(record)

    successful = [
        r for r in all_results
        if r["status"] == "success"
    ]

    errors = [
        r for r in all_results
        if r["status"] == "error"
    ]

    total_packages = sum(
        r.get("total_packages", 0)
        for r in successful
    )

    total_action_correct = sum(
        r.get("action_correct", 0)
        for r in successful
    )

    total_exact_correct = sum(
        r.get("exact_correct", 0)
        for r in successful
    )

    case_action_perfect = sum(
        1
        for r in successful
        if r.get("total_packages", 0) > 0
        and r.get("action_correct", 0) == r.get("total_packages", 0)
    )

    case_exact_perfect = sum(
        1
        for r in successful
        if r.get("total_packages", 0) > 0
        and r.get("exact_correct", 0) == r.get("total_packages", 0)
    )

    metrics = {
        "evaluation": "Agent 4 Groq baseline",
        "model": provider.model,
        "provider": "Groq",
        "dataset_version": dataset["dataset_metadata"].get("version"),
        "dataset_cases": len(cases),
        "dataset_sha256": dataset_hash,

        "cases_successful": len(successful),
        "cases_with_errors": len(errors),

        "total_packages_evaluated": total_packages,

        "action_accuracy": (
            total_action_correct / total_packages
            if total_packages else None
        ),

        "exact_recommendation_accuracy": (
            total_exact_correct / total_packages
            if total_packages else None
        ),

        "case_level_action_accuracy": (
            case_action_perfect / len(successful)
            if successful else None
        ),

        "case_level_exact_accuracy": (
            case_exact_perfect / len(successful)
            if successful else None
        ),

        "mean_latency_seconds": (
            sum(r["latency_seconds"] for r in successful) / len(successful)
            if successful else None
        ),

        "total_latency_seconds": (
            sum(r["latency_seconds"] for r in successful)
            if successful else None
        ),
    }

    raw_path = OUT_DIR / "groq_baseline_raw_results.json"
    metrics_path = OUT_DIR / "groq_baseline_metrics.json"

    output = {
        "metadata": {
            "evaluation": "baseline",
            "provider": "Groq",
            "model": provider.model,
            "dataset_version": dataset["dataset_metadata"].get("version"),
            "dataset_sha256": dataset_hash,
            "total_cases": len(cases),
        },
        "metrics": metrics,
        "cases": all_results,
    }

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("\n")
    print("=" * 72)
    print("BASELINE COMPLETE")
    print("=" * 72)

    for key, value in metrics.items():
        print(f"{key}: {value}")

    print("\nFiles:")
    print(raw_path)
    print(metrics_path)


if __name__ == "__main__":
    main()
