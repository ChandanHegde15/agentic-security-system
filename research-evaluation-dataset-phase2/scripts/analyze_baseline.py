import json
import csv
from pathlib import Path
from collections import Counter, defaultdict

BASE = Path(r"D:\MAJOR PROJECT")

PHASE2 = BASE / "research-evaluation-dataset-phase2"
RESULTS_DIR = PHASE2 / "baseline_results"

RESULTS = RESULTS_DIR / "groq_baseline_raw_results_corrected.json"
DATASET = PHASE2 / "research_evaluation_dataset.json"

REPORT_JSON = RESULTS_DIR / "baseline_failure_analysis.json"
REPORT_TXT = RESULTS_DIR / "baseline_failure_analysis.txt"
CASE_CSV = RESULTS_DIR / "baseline_case_summary.csv"
PACKAGE_CSV = RESULTS_DIR / "baseline_package_failures.csv"


# ============================================================
# LOAD FILES
# ============================================================

with open(RESULTS, "r", encoding="utf-8") as f:
    data = json.load(f)

with open(DATASET, "r", encoding="utf-8") as f:
    dataset = json.load(f)


cases = data["cases"]
dataset_cases = dataset["cases"]


# ============================================================
# RECOVER CATEGORY / SUBCATEGORY
# ============================================================

dataset_lookup = {
    c["case_id"]: c
    for c in dataset_cases
}

for case in cases:
    source = dataset_lookup.get(case["case_id"])

    if source:
        case.setdefault("category", source.get("category"))
        case.setdefault("subcategory", source.get("subcategory"))


# ============================================================
# BASIC METRICS
# ============================================================

total_cases = len(cases)

successful_cases = sum(
    c.get("status") == "success"
    for c in cases
)

failed_execution = sum(
    c.get("status") != "success"
    for c in cases
)

total_packages = sum(
    c.get("total_packages", 0)
    for c in cases
)

action_correct = sum(
    c.get("action_correct", 0)
    for c in cases
)

exact_correct = sum(
    c.get("exact_correct", 0)
    for c in cases
)

action_accuracy = (
    action_correct / total_packages
    if total_packages
    else 0
)

exact_accuracy = (
    exact_correct / total_packages
    if total_packages
    else 0
)

case_level_action_correct = sum(
    c.get("action_correct", 0) == c.get("total_packages", 0)
    for c in cases
)

case_level_exact_correct = sum(
    c.get("exact_correct", 0) == c.get("total_packages", 0)
    for c in cases
)

case_level_action_accuracy = (
    case_level_action_correct / total_cases
    if total_cases
    else 0
)

case_level_exact_accuracy = (
    case_level_exact_correct / total_cases
    if total_cases
    else 0
)

latencies = [
    c["latency_seconds"]
    for c in cases
    if "latency_seconds" in c
]

mean_latency = (
    sum(latencies) / len(latencies)
    if latencies
    else 0
)

min_latency = min(latencies) if latencies else 0
max_latency = max(latencies) if latencies else 0
total_latency = sum(latencies)


# ============================================================
# FAILED CASES
# ============================================================

failed_cases = [
    c
    for c in cases
    if c.get("action_correct", 0) < c.get("total_packages", 0)
]


# ============================================================
# CATEGORY ANALYSIS
# ============================================================

category_stats = defaultdict(
    lambda: {
        "cases": 0,
        "failed_cases": 0,
        "packages": 0,
        "action_correct": 0,
        "exact_correct": 0,
    }
)

for c in cases:
    category = c.get("category", "unknown")

    s = category_stats[category]

    s["cases"] += 1
    s["packages"] += c.get("total_packages", 0)
    s["action_correct"] += c.get("action_correct", 0)
    s["exact_correct"] += c.get("exact_correct", 0)

    if c.get("action_correct", 0) < c.get("total_packages", 0):
        s["failed_cases"] += 1


category_report = {}

for category, s in category_stats.items():
    category_report[category] = {
        **s,
        "action_accuracy": (
            s["action_correct"] / s["packages"]
            if s["packages"]
            else 0
        ),
        "exact_accuracy": (
            s["exact_correct"] / s["packages"]
            if s["packages"]
            else 0
        ),
    }


# ============================================================
# SUBCATEGORY ANALYSIS
# ============================================================

subcategory_stats = defaultdict(
    lambda: {
        "cases": 0,
        "failed_cases": 0,
        "packages": 0,
        "action_correct": 0,
        "exact_correct": 0,
    }
)

for c in cases:
    category = c.get("category", "unknown")
    subcategory = c.get("subcategory", "unknown")

    key = f"{category}/{subcategory}"

    s = subcategory_stats[key]

    s["cases"] += 1
    s["packages"] += c.get("total_packages", 0)
    s["action_correct"] += c.get("action_correct", 0)
    s["exact_correct"] += c.get("exact_correct", 0)

    if c.get("action_correct", 0) < c.get("total_packages", 0):
        s["failed_cases"] += 1


subcategory_report = {}

for key, s in subcategory_stats.items():
    subcategory_report[key] = {
        **s,
        "action_accuracy": (
            s["action_correct"] / s["packages"]
            if s["packages"]
            else 0
        ),
        "exact_accuracy": (
            s["exact_correct"] / s["packages"]
            if s["packages"]
            else 0
        ),
    }


# ============================================================
# PACKAGE-LEVEL FAILURES
# ============================================================

package_failures = []

for c in cases:
    for comparison in c.get("package_comparisons", []):

        if not comparison.get("action_match", False):

            package_failures.append({
                "case_id": c["case_id"],
                "category": c.get("category", "unknown"),
                "subcategory": c.get("subcategory", "unknown"),
                "package_name": comparison.get("package_name"),
                "expected_action": comparison.get("expected_action"),
                "predicted_action": comparison.get("predicted_action"),
                "expected_suggested_package":
                    comparison.get("expected_suggested_package"),
                "predicted_suggested_package":
                    comparison.get("predicted_suggested_package"),
                "expected_evidence":
                    comparison.get("expected_evidence"),
                "predicted_evidence":
                    comparison.get("predicted_evidence"),
                "exact_match":
                    comparison.get("exact_match"),
            })


# ============================================================
# ACTION DISTRIBUTION
# ============================================================

predicted_actions = Counter()
expected_actions = Counter()

for c in cases:
    for comparison in c.get("package_comparisons", []):

        predicted = comparison.get("predicted_action")
        expected = comparison.get("expected_action")

        if predicted:
            predicted_actions[predicted] += 1

        if expected:
            expected_actions[expected] += 1


# ============================================================
# FAILED CASE SUMMARY
# ============================================================

failed_case_report = []

for c in failed_cases:
    failed_case_report.append({
        "case_id": c["case_id"],
        "category": c.get("category", "unknown"),
        "subcategory": c.get("subcategory", "unknown"),
        "action_correct": c.get("action_correct", 0),
        "total_packages": c.get("total_packages", 0),
        "exact_correct": c.get("exact_correct", 0),
        "action_accuracy": (
            c.get("action_correct", 0)
            / c.get("total_packages", 1)
        ),
        "exact_accuracy": (
            c.get("exact_correct", 0)
            / c.get("total_packages", 1)
        ),
    })


# ============================================================
# COMPLETE REPORT OBJECT
# ============================================================

report = {
    "evaluation": data.get("metadata", {}).get(
        "evaluation",
        "Agent 4 Groq baseline"
    ),
    "model": data.get("metadata", {}).get(
        "model",
        "openai/gpt-oss-20b"
    ),
    "provider": data.get("metadata", {}).get(
        "provider",
        "Groq"
    ),

    "dataset": {
        "cases": total_cases,
        "dataset_version": data.get("metadata", {}).get(
            "dataset_version",
            "1.1.0"
        ),
        "dataset_sha256": data.get("metadata", {}).get(
            "dataset_sha256"
        ),
    },

    "execution": {
        "cases_total": total_cases,
        "cases_successful": successful_cases,
        "cases_with_execution_errors": failed_execution,
    },

    "overall_metrics": {
        "packages_evaluated": total_packages,
        "action_correct": action_correct,
        "action_accuracy": action_accuracy,
        "exact_correct": exact_correct,
        "exact_accuracy": exact_accuracy,
        "fully_action_correct_cases": case_level_action_correct,
        "case_level_action_accuracy": case_level_action_accuracy,
        "fully_exact_correct_cases": case_level_exact_correct,
        "case_level_exact_accuracy": case_level_exact_accuracy,
    },

    "latency": {
        "mean_seconds": mean_latency,
        "minimum_seconds": min_latency,
        "maximum_seconds": max_latency,
        "total_seconds": total_latency,
    },

    "failed_cases": failed_case_report,

    "failed_package_count": len(package_failures),

    "category_analysis": category_report,

    "subcategory_analysis": subcategory_report,

    "predicted_action_distribution":
        dict(predicted_actions),

    "expected_action_distribution":
        dict(expected_actions),

    "case_004_recovery": {
        "included": any(
            c["case_id"] == "CASE-004"
            for c in cases
        ),
        "status": next(
            (
                c.get("status")
                for c in cases
                if c["case_id"] == "CASE-004"
            ),
            None,
        ),
    },

    "research_note": (
        "The 65-case evaluation benchmark is treated as frozen and "
        "unseen for subsequent Agent 4 fine-tuning. CASE-004 was "
        "initially affected by a Groq rate-limit execution error and "
        "was subsequently evaluated separately and merged into the "
        "corrected baseline results."
    ),
}


# ============================================================
# SAVE JSON
# ============================================================

with open(REPORT_JSON, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)


# ============================================================
# SAVE CASE CSV
# ============================================================

with open(
    CASE_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "case_id",
            "category",
            "subcategory",
            "status",
            "total_packages",
            "action_correct",
            "action_accuracy",
            "exact_correct",
            "exact_accuracy",
            "latency_seconds",
        ],
    )

    writer.writeheader()

    for c in cases:
        packages = c.get("total_packages", 0)

        writer.writerow({
            "case_id": c["case_id"],
            "category": c.get("category", "unknown"),
            "subcategory": c.get("subcategory", "unknown"),
            "status": c.get("status"),
            "total_packages": packages,
            "action_correct": c.get("action_correct", 0),
            "action_accuracy": (
                c.get("action_correct", 0) / packages
                if packages
                else 1
            ),
            "exact_correct": c.get("exact_correct", 0),
            "exact_accuracy": (
                c.get("exact_correct", 0) / packages
                if packages
                else 1
            ),
            "latency_seconds": c.get("latency_seconds"),
        })


# ============================================================
# SAVE PACKAGE FAILURE CSV
# ============================================================

with open(
    PACKAGE_CSV,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    fieldnames = [
        "case_id",
        "category",
        "subcategory",
        "package_name",
        "expected_action",
        "predicted_action",
        "expected_suggested_package",
        "predicted_suggested_package",
        "expected_evidence",
        "predicted_evidence",
        "exact_match",
    ]

    writer = csv.DictWriter(
        f,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for row in package_failures:
        writer.writerow({
            **row,
            "expected_evidence":
                ",".join(row["expected_evidence"] or []),
            "predicted_evidence":
                ",".join(row["predicted_evidence"] or []),
        })


# ============================================================
# SAVE HUMAN-READABLE REPORT
# ============================================================

with open(REPORT_TXT, "w", encoding="utf-8") as f:

    f.write("=" * 90 + "\n")
    f.write("AGENT 4 GROQ BASELINE - COMPLETE FAILURE ANALYSIS\n")
    f.write("=" * 90 + "\n\n")

    f.write("BASELINE OVERVIEW\n")
    f.write("-" * 90 + "\n")
    f.write(f"Total cases                 : {total_cases}\n")
    f.write(f"Successful executions       : {successful_cases}\n")
    f.write(f"Execution errors            : {failed_execution}\n")
    f.write(f"Packages evaluated          : {total_packages}\n")
    f.write(f"Action correct              : {action_correct}\n")
    f.write(f"Action accuracy             : {action_accuracy:.4%}\n")
    f.write(f"Exact correct               : {exact_correct}\n")
    f.write(f"Exact accuracy              : {exact_accuracy:.4%}\n")
    f.write(
        f"Fully correct cases         : "
        f"{case_level_action_correct}/{total_cases}\n"
    )
    f.write(
        f"Case-level action accuracy  : "
        f"{case_level_action_accuracy:.4%}\n"
    )
    f.write(
        f"Case-level exact accuracy   : "
        f"{case_level_exact_accuracy:.4%}\n"
    )
    f.write(f"Mean latency                : {mean_latency:.4f}s\n")
    f.write(f"Minimum latency             : {min_latency:.4f}s\n")
    f.write(f"Maximum latency             : {max_latency:.4f}s\n")
    f.write(f"Total latency               : {total_latency:.4f}s\n")

    f.write("\n")
    f.write("=" * 90 + "\n")
    f.write("CASE-LEVEL RESULTS\n")
    f.write("=" * 90 + "\n")

    for c in cases:
        passed = (
            c.get("action_correct", 0)
            == c.get("total_packages", 0)
        )

        f.write(
            f"{c['case_id']} | "
            f"{c.get('category', 'unknown')} | "
            f"{c.get('subcategory', 'unknown')} | "
            f"{c.get('action_correct', 0)}/"
            f"{c.get('total_packages', 0)} | "
            f"{'PASS' if passed else 'FAIL'}\n"
        )

    f.write("\n")
    f.write("=" * 90 + "\n")
    f.write(f"FAILED CASES: {len(failed_cases)}\n")
    f.write("=" * 90 + "\n")

    for c in failed_cases:
        f.write(
            f"{c['case_id']} | "
            f"{c.get('category', 'unknown')} | "
            f"{c.get('subcategory', 'unknown')} | "
            f"action={c.get('action_correct', 0)}/"
            f"{c.get('total_packages', 0)} | "
            f"exact={c.get('exact_correct', 0)}/"
            f"{c.get('total_packages', 0)}\n"
        )

    f.write("\n")
    f.write("=" * 90 + "\n")
    f.write("FAILURES BY CATEGORY\n")
    f.write("=" * 90 + "\n")

    for category, s in category_report.items():
        f.write(
            f"{category}: "
            f"cases={s['cases']}, "
            f"failed_cases={s['failed_cases']}, "
            f"packages={s['packages']}, "
            f"action_accuracy={s['action_accuracy']:.4%}, "
            f"exact_accuracy={s['exact_accuracy']:.4%}\n"
        )

    f.write("\n")
    f.write("=" * 90 + "\n")
    f.write("FAILURES BY SUBCATEGORY\n")
    f.write("=" * 90 + "\n")

    for key, s in subcategory_report.items():
        f.write(
            f"{key}: "
            f"cases={s['cases']}, "
            f"failed_cases={s['failed_cases']}, "
            f"packages={s['packages']}, "
            f"action_accuracy={s['action_accuracy']:.4%}, "
            f"exact_accuracy={s['exact_accuracy']:.4%}\n"
        )

    f.write("\n")
    f.write("=" * 90 + "\n")
    f.write("PACKAGE-LEVEL ACTION FAILURES\n")
    f.write("=" * 90 + "\n")

    for row in package_failures:
        f.write(
            f"{row['case_id']} | "
            f"{row['package_name']} | "
            f"expected={row['expected_action']} | "
            f"predicted={row['predicted_action']} | "
            f"exact={row['exact_match']}\n"
        )

    f.write(
        f"\nTotal package-level action failures: "
        f"{len(package_failures)}\n"
    )

    f.write("\n")
    f.write("=" * 90 + "\n")
    f.write("PREDICTED ACTION DISTRIBUTION\n")
    f.write("=" * 90 + "\n")

    for action, count in predicted_actions.most_common():
        f.write(f"{action}: {count}\n")

    f.write("\n")
    f.write("=" * 90 + "\n")
    f.write("EXPECTED ACTION DISTRIBUTION\n")
    f.write("=" * 90 + "\n")

    for action, count in expected_actions.most_common():
        f.write(f"{action}: {count}\n")

    f.write("\n")
    f.write("=" * 90 + "\n")
    f.write("CASE-004 RECOVERY\n")
    f.write("=" * 90 + "\n")

    c4 = next(
        (c for c in cases if c["case_id"] == "CASE-004"),
        None,
    )

    if c4:
        f.write(
            f"Status          : {c4.get('status')}\n"
            f"Category        : {c4.get('category')}\n"
            f"Subcategory     : {c4.get('subcategory')}\n"
            f"Action correct  : {c4.get('action_correct')}/"
            f"{c4.get('total_packages')}\n"
            f"Exact correct   : {c4.get('exact_correct')}/"
            f"{c4.get('total_packages')}\n"
            f"Latency         : {c4.get('latency_seconds')}s\n"
        )

    f.write("\n")
    f.write("=" * 90 + "\n")
    f.write("RESEARCH STATUS\n")
    f.write("=" * 90 + "\n")
    f.write(
        "The 65-case benchmark remains the frozen external evaluation "
        "benchmark. It must not be used as Agent 4 fine-tuning data.\n"
    )
    f.write(
        "CASE-004 was initially affected by a Groq rate-limit error and "
        "was subsequently executed separately and merged into the "
        "corrected baseline.\n"
    )
    f.write(
        "The next research stage is failure analysis followed by creation "
        "of a separate Agent 4 fine-tuning dataset.\n"
    )


# ============================================================
# CONSOLE SUMMARY
# ============================================================

print("=" * 80)
print("BASELINE FAILURE ANALYSIS COMPLETE")
print("=" * 80)

print(f"Cases                  : {total_cases}")
print(f"Successful executions  : {successful_cases}")
print(f"Execution errors       : {failed_execution}")
print(f"Packages evaluated     : {total_packages}")
print(f"Action accuracy        : {action_accuracy:.4%}")
print(f"Exact accuracy         : {exact_accuracy:.4%}")
print(
    f"Case-level accuracy    : "
    f"{case_level_action_accuracy:.4%}"
)
print(f"Failed cases           : {len(failed_cases)}")
print(f"Package failures       : {len(package_failures)}")

print()
print("FILES CREATED")
print("-" * 80)
print(REPORT_JSON)
print(REPORT_TXT)
print(CASE_CSV)
print(PACKAGE_CSV)
print()
print("No benchmark cases were rerun.")