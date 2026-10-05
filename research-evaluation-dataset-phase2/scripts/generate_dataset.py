#!/usr/bin/env python3
"""Dataset generator for the Agentic Security System evaluation dataset."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping

# The dataset package is independent of the implementation repository.
# Supply the repository explicitly via AGENTIC_SECURITY_REPO.
REPO_ROOT = Path(os.environ.get("AGENTIC_SECURITY_REPO", "")).expanduser().resolve()
if not REPO_ROOT.is_dir():
    raise RuntimeError(
        "Set AGENTIC_SECURITY_REPO to the root of the agentic-security-system repository before generating the dataset."
    )
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Mock groq module before importing recommendation agents to prevent collection errors
import unittest.mock
if "groq" not in sys.modules:
    sys.modules["groq"] = unittest.mock.MagicMock()

from agents.dependency_extraction.agent import extract_dependencies
from agents.registry_verification.agent import verify_extraction
from agents.registry_verification.registries.pypi_client import RegistryClientError
from agents.risk_analysis.analyzer import RiskAnalyzer, RiskPolicy, analyze_verification
from agents.recommendation.models import (
    Recommendation,
    RecommendationAction,
    RecommendationResult,
)
from agents.recommendation.validation import (
    RecommendationValidationError,
    validate_recommendation,
)
from agents.recommendation_verification.agent import RecommendationVerifier
from agents.recommendation_verification.models import VerificationStatus
from agents.recommendation_verification.validation import (
    RecommendationVerificationError,
    validate_inputs,
)


class StubClient:
    """Mock registry client providing deterministic package metadata or errors."""
    def __init__(self, outcomes: dict[str, Any]) -> None:
        self.outcomes = outcomes

    def get_package_metadata(self, package_name: str):
        if package_name not in self.outcomes:
            return None
        outcome = self.outcomes[package_name]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def runner_without_installs(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    if command[0] == "git":
        return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return subprocess.CompletedProcess(command, 0, "", "")


def runner_with_failure(failing_fragment: str):
    def runner(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        if command[0] == "git":
            return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
        if failing_fragment in command:
            return subprocess.CompletedProcess(command, 1, "", f"simulated failure: {failing_fragment}")
        return subprocess.CompletedProcess(command, 0, "", "")
    return runner


def create_git_project(project_dir: Path, files: dict[str, str]) -> None:
    """Initialize a git repository in project_dir with given files."""
    def git(*args):
        subprocess.run(["git", *args], cwd=project_dir, check=True, capture_output=True, text=True)
    git("init", "-b", "main")
    git("config", "user.email", "eval@example.invalid")
    git("config", "user.name", "Dataset Evaluator")
    for name, content in files.items():
        file_path = project_dir / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "Initial commit")


def run_case_generation(case_def: dict[str, Any]) -> dict[str, Any]:
    """Execute the repository pipeline for one scenario and return the standardized case record."""
    case_id = case_def["case_id"]
    category = case_def["category"]
    subcategory = case_def["subcategory"]
    description = case_def["description"]
    is_negative = case_def.get("is_negative_test", False)
    expected_rejection_stage = case_def.get("expected_rejection_stage")
    files = case_def["files"]
    project_id = case_def.get("project_id", case_id)
    registry_pypi = case_def.get("registry_pypi", {})
    registry_npm = case_def.get("registry_npm", {})
    custom_ref_pkgs = case_def.get("custom_reference_packages")
    custom_policy = case_def.get("custom_risk_policy")
    agent4_action = case_def.get("agent4_action")
    agent4_suggested_package = case_def.get("agent4_suggested_package")
    agent4_evidence_referenced = case_def.get("agent4_evidence_referenced")
    agent4_conditional = case_def.get("agent4_conditional", False)
    agent4_confidence = case_def.get("agent4_confidence", 0.9)
    agent4_artifact_under_test = case_def.get("agent4_artifact_under_test")
    remediation_runner_type = case_def.get("remediation_runner", "normal")

    with tempfile.TemporaryDirectory(prefix=f"eval-{case_id}-") as tmp_dir:
        proj_path = Path(tmp_dir) / project_id
        proj_path.mkdir(parents=True)
        create_git_project(proj_path, files)

        # 1. Agent 1: Dependency Extraction
        agent_1_result = extract_dependencies(proj_path)

        # 2. Agent 2: Registry Verification
        pypi_client = StubClient(registry_pypi)
        npm_client = StubClient(registry_npm)
        agent_2_result = verify_extraction(agent_1_result, pypi_client=pypi_client, npm_client=npm_client)

        # 3. Agent 3: Risk Analysis
        agent_3_result = analyze_verification(
            agent_2_result,
            reference_packages=custom_ref_pkgs,
            policy=custom_policy,
        )

        # 4. Agent 4 & Agent 5
        agent_4_ground_truth = None
        agent_5_ground_truth = None
        candidate_remediation_ground_truth = None

        if not is_negative:
            # Construct valid Agent 4 recommendation
            if "agent4_recommendations" in case_def:
                raw_recs = [
                    Recommendation(**item) for item in case_def["agent4_recommendations"]
                ]
            else:
                dep_name = agent_3_result["dependencies"][0]["package_name"] if agent_3_result["dependencies"] else "none"
                if agent_3_result["dependencies"]:
                    dep_rec = agent_3_result["dependencies"][0]
                    signals = dep_rec.get("signals", [])
                    if agent4_evidence_referenced is None:
                        agent4_evidence_referenced = [s["type"] for s in signals]
                    if agent4_action == "replace" and not agent4_suggested_package:
                        ref_pkg = next((s.get("reference_package") for s in signals if s.get("reference_package")), None)
                        agent4_suggested_package = ref_pkg
                else:
                    agent4_evidence_referenced = []
                raw_recs = [
                    Recommendation(
                        package_name=dep_name,
                        action=agent4_action or RecommendationAction.NO_ACTION,
                        suggested_package=agent4_suggested_package,
                        suggested_version=None,
                        confidence=agent4_confidence,
                        reasoning="Placeholder reasoning to be regenerated",
                        evidence_referenced=agent4_evidence_referenced or [],
                        conditional=agent4_conditional,
                    )
                ] if agent_3_result["dependencies"] else []

            rec_obj = RecommendationResult(project_id=project_id, recommendations=raw_recs)
            validated_rec = validate_recommendation(rec_obj, agent_3_result)
            agent_4_ground_truth = validated_rec.model_dump(mode="json")

            # Agent 5 Execution
            if remediation_runner_type == "normal":
                runner = runner_without_installs
            elif remediation_runner_type == "test_failure":
                runner = runner_with_failure("pytest")
            elif remediation_runner_type == "install_failure":
                runner = runner_with_failure("pip")
            elif remediation_runner_type == "branch_collision":
                runner = runner_without_installs
                verifier = RecommendationVerifier(runner_without_installs)
                bname = verifier._branch_name(project_id, validated_rec)
                subprocess.run(["git", "branch", bname], cwd=proj_path, check=True, capture_output=True, text=True)
            elif remediation_runner_type == "unexpected_modifications":
                def runner(command: list[str], cwd: Path):
                    if command[:4] == ["git", "worktree", "add", "-b"]:
                        res = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
                        target_dir = Path(command[5])
                        (target_dir / "untracked_modification.txt").write_text("rogue file")
                        return res
                    if command[0] == "git":
                        return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
                    return subprocess.CompletedProcess(command, 0, "", "")
            else:
                runner = runner_without_installs

            verifier = RecommendationVerifier(runner)
            try:
                a5_res = verifier.verify(agent_3_result, validated_rec, proj_path)
                agent_5_ground_truth = a5_res.model_dump(mode="json")
                has_replace = any(r.action is RecommendationAction.REPLACE for r in validated_rec.recommendations)
                is_reqs = False
                if has_replace:
                    is_reqs = any(
                        agent_3_result["dependencies"][i]["source_file"] == "requirements.txt"
                        for i, r in enumerate(validated_rec.recommendations)
                        if r.action is RecommendationAction.REPLACE
                    )
                candidate_remediation_ground_truth = {
                    "candidate_created": bool(a5_res.branch_name and a5_res.candidate_valid),
                    "branch_name": a5_res.branch_name,
                    "dependency_declaration_changed": bool(a5_res.branch_name and is_reqs and remediation_runner_type != "branch_collision"),
                    "installation_succeeded": True if (a5_res.tests_available or a5_res.status == VerificationStatus.VERIFIED or (a5_res.status == VerificationStatus.REJECTED and a5_res.tests_passed is False)) else (False if remediation_runner_type == "install_failure" else None),
                    "tests_available": a5_res.tests_available,
                    "tests_passed": a5_res.tests_passed,
                    "candidate_valid": a5_res.candidate_valid,
                    "merge_allowed": a5_res.merge_allowed,
                    "failure_reason": a5_res.details[0] if (not a5_res.merge_allowed and a5_res.details) else None,
                }
            except RecommendationVerificationError as error:
                agent_5_ground_truth = None
                candidate_remediation_ground_truth = {
                    "candidate_created": False,
                    "branch_name": None,
                    "dependency_declaration_changed": False,
                    "installation_succeeded": None,
                    "tests_available": False,
                    "tests_passed": None,
                    "candidate_valid": False,
                    "merge_allowed": False,
                    "failure_reason": f"Agent 5 input validation rejected recommendation: {error}",
                }
        else:
            # Negative tests are executed against the actual validation layer
            # they claim to exercise. This makes rejection stage and error text
            # reproducible rather than relying on hand-written expectations.
            artifact = agent4_artifact_under_test
            if artifact is None:
                raise ValueError(f"{case_id}: negative case is missing agent4_artifact_under_test")
            rejection_stage = expected_rejection_stage or "agent4"
            rejection_error = None
            validated_negative = None
            try:
                artifact_result = RecommendationResult.model_validate(artifact)
            except (RecommendationValidationError, ValueError) as error:
                rejection_error = str(error).rstrip(".")
                rejection_stage = "agent4"
            if rejection_error is None and rejection_stage == "agent4":
                try:
                    validate_recommendation(artifact_result, agent_3_result)
                except (RecommendationValidationError, ValueError) as error:
                    rejection_error = str(error).rstrip(".")
                    rejection_stage = "agent4"
            if rejection_error is None and rejection_stage == "agent5":
                try:
                    # Agent 5 must validate the raw Agent 4 artifact. Do not
                    # run Agent 4's normalizer first, because that would erase
                    # malformed reasoning that this negative case is testing.
                    validate_inputs(agent_3_result, artifact_result)
                except RecommendationVerificationError as error:
                    rejection_error = str(error).rstrip(".")
                    rejection_stage = "agent5"
            if rejection_error is None:
                raise AssertionError(f"{case_id}: expected negative rejection was not reproduced")
            candidate_remediation_ground_truth = {
                "candidate_created": False,
                "branch_name": None,
                "dependency_declaration_changed": False,
                "installation_succeeded": None,
                "tests_available": False,
                "tests_passed": None,
                "candidate_valid": False,
                "merge_allowed": False,
                "failure_reason": f"Rejected during {rejection_stage} validation: {rejection_error}",
            }
            agent_5_ground_truth = None
            agent_4_ground_truth = None
            negative_validation = {
                "expected_stage": expected_rejection_stage,
                "actual_stage": rejection_stage,
                "error": rejection_error,
                "matched": rejection_stage == expected_rejection_stage,
            }

        return {
            "case_id": case_id,
            "category": category,
            "subcategory": subcategory,
            "description": description,
            "is_negative_test": is_negative,
            "provenance": {
                "agent_1_source": "executed_agent_1_extract_dependencies",
                "agent_2_source": "executed_agent_2_verify_extraction_with_stubs",
                "agent_3_source": "executed_agent_3_analyze_verification",
                "agent_4_source": "executed_agent_4_validate_recommendation" if (not is_negative or expected_rejection_stage == "agent4") else "executed_agent_4_validate_recommendation_then_agent5",
                "agent_5_source": "executed_agent_5_input_validation" if (is_negative and expected_rejection_stage == "agent5") else ("not_reached" if is_negative else "executed_agent_5_recommendation_verifier"),
                "candidate_remediation_source": "not_reached_negative_validation" if is_negative else ("fault_injected_command_runner" if remediation_runner_type != "normal" else "executed_agent_5_isolated_remediation"),
            },
            "configuration": {
                "custom_reference_packages": custom_ref_pkgs,
                "custom_risk_policy": {
                    "not_found_weight": custom_policy.not_found_weight,
                    "moderate_similarity_weight": custom_policy.moderate_similarity_weight,
                    "strong_similarity_weight": custom_policy.strong_similarity_weight,
                    "moderate_similarity_threshold": custom_policy.moderate_similarity_threshold,
                    "strong_similarity_threshold": custom_policy.strong_similarity_threshold,
                    "low_max": custom_policy.low_max,
                    "medium_max": custom_policy.medium_max,
                    "high_max": custom_policy.high_max,
                } if custom_policy else None,
            },
            "project_input": {
                "project_id": project_id,
                "files": files,
            },
            "agent_1_ground_truth": agent_1_result,
            "agent_2_ground_truth": agent_2_result,
            "agent_3_ground_truth": agent_3_result,
            "agent_4_ground_truth": agent_4_ground_truth,
            "agent_4_artifact_under_test": agent4_artifact_under_test,
            "negative_validation": negative_validation if is_negative else None,
            "agent_5_ground_truth": agent_5_ground_truth,
            "candidate_remediation_ground_truth": candidate_remediation_ground_truth,
        }


def main():
    from cases_data import CASES_DEFINITIONS

    print(f"Generating research evaluation dataset for {len(CASES_DEFINITIONS)} cases...")
    cases = []
    for i, case_def in enumerate(CASES_DEFINITIONS, start=1):
        case_id = case_def["case_id"]
        print(f"[{i:02d}/{len(CASES_DEFINITIONS):02d}] Processing {case_id} ({case_def['category']}/{case_def['subcategory']})...")
        case_record = run_case_generation(case_def)
        cases.append(case_record)

    dataset = {
        "dataset_metadata": {
            "version": "1.1.0",
            "total_cases": len(cases),
            "description": "Complete research-quality evaluation dataset for Agentic Security System",
            "repository": "https://github.com/ChandanHegde15/agentic-security-system",
            "generator": "Antigravity Research Evaluation Pipeline",
            "scoring_policy_defaults": {
                "not_found_weight": 50,
                "moderate_similarity_weight": 20,
                "strong_similarity_weight": 40,
                "moderate_similarity_threshold": 0.80,
                "strong_similarity_threshold": 0.90,
                "low_max": 19,
                "medium_max": 49,
                "high_max": 74,
            },
            "reference_package_defaults": {
                "pypi": ["requests", "numpy", "pandas", "flask"],
                "npm": ["express", "axios", "react"],
            },
        },
        "cases": cases,
    }

    out_file = REPO_ROOT / "dataset" / "research_evaluation_dataset.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"\nSUCCESS: Generated {len(cases)} cases written to {out_file}")
    print(f"Total file size: {out_file.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

