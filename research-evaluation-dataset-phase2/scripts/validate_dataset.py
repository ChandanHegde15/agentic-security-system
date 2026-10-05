#!/usr/bin/env python3
"""Validation script for the generated research evaluation dataset.

Performs all 22 required internal consistency checks, schema validations,
Agent 3 reproducibility checks, and negative case expectation verifications.
"""

import json
import sys
import unittest.mock
from pathlib import Path
from typing import Any

# The validator is packaged separately from the implementation repository.
# Supply the repository explicitly via AGENTIC_SECURITY_REPO.
import os
REPO_ROOT = Path(os.environ.get("AGENTIC_SECURITY_REPO", "")).expanduser().resolve()
if not REPO_ROOT.is_dir():
    raise RuntimeError(
        "Set AGENTIC_SECURITY_REPO to the root of the agentic-security-system repository before validating the dataset."
    )
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Mock groq module before importing recommendation agents
if "groq" not in sys.modules:
    sys.modules["groq"] = unittest.mock.MagicMock()

from agents.dependency_extraction.models import ExtractionResult, Dependency
from agents.registry_verification.models import VerificationResult as A2VerificationResult, VerificationRecord as A2VerificationRecord
from agents.risk_analysis.analyzer import RiskAnalyzer, RiskPolicy, analyze_verification
from agents.risk_analysis.models import RiskResult as A3RiskResult
from agents.recommendation.models import Agent3RiskResult, RecommendationResult, Recommendation
from agents.recommendation.validation import validate_agent3_input, validate_recommendation, RecommendationValidationError
from agents.recommendation_verification.models import VerificationResult as A5VerificationResult, VerificationStatus
from agents.recommendation_verification.validation import validate_inputs, RecommendationVerificationError


def validate_dataset(dataset_path: Path) -> dict[str, Any]:
    print(f"Loading dataset from {dataset_path}...")
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    metadata = data.get("dataset_metadata", {})
    cases = data.get("cases", [])
    total_cases = len(cases)
    print(f"Found {total_cases} cases in dataset.")

    results = {
        "total_cases": total_cases,
        "valid_json": True,
        "schema_validation_passed": 0,
        "agent1_consistency_passed": 0,
        "agent2_consistency_passed": 0,
        "agent3_reproducibility_passed": 0,
        "agent4_evidence_consistency_passed": 0,
        "agent5_validation_passed": 0,
        "candidate_remediation_consistency_passed": 0,
        "security_claim_safety_passed": 0,
        "negative_validation_passed": 0,
        "negative_stage_validation_passed": 0,
        "errors": [],
    }

    FORBIDDEN_TERMS = ["malicious", "malware", "compromised", "typo-squatting", "typosquatting"]

    for i, case in enumerate(cases, start=1):
        cid = case.get("case_id", f"case_{i}")
        is_negative = case.get("is_negative_test", False)

        try:
            # 1. Schema Validation
            # Agent 1
            a1_data = case["agent_1_ground_truth"]
            assert isinstance(a1_data["project_id"], str)
            assert isinstance(a1_data["dependencies"], list)
            for d in a1_data["dependencies"]:
                Dependency(**d)

            # Agent 2
            a2_data = case["agent_2_ground_truth"]
            assert isinstance(a2_data["project_id"], str)
            assert isinstance(a2_data["dependencies"], list)
            for d in a2_data["dependencies"]:
                A2VerificationRecord(**d)

            # Agent 3
            a3_data = case["agent_3_ground_truth"]
            assert isinstance(a3_data["project_id"], str)
            validate_agent3_input(a3_data)

            # Agent 4 & 5 (for valid cases)
            if not is_negative:
                a4_data = case["agent_4_ground_truth"]
                assert a4_data is not None
                RecommendationResult.model_validate(a4_data)

                a5_data = case["agent_5_ground_truth"]
                if a5_data is not None:
                    A5VerificationResult.model_validate(a5_data)
            else:
                # Negative case: verify the artifact and its actual rejection stage.
                artifact = case.get("agent_4_artifact_under_test")
                assert artifact is not None
                assert case.get("agent_4_ground_truth") is None
                negative_validation = case.get("negative_validation")
                assert negative_validation is not None
                assert negative_validation.get("matched") is True, f"{cid}: negative rejection stage mismatch"
                assert negative_validation.get("actual_stage") in {"agent4", "agent5"}
                if negative_validation["actual_stage"] == "agent4":
                    try:
                        artifact_result = RecommendationResult.model_validate(artifact)
                    except Exception:
                        # Schema-invalid Agent 4 artifacts are valid negative tests.
                        pass
                    else:
                        try:
                            validate_recommendation(artifact_result, a3_data)
                        except RecommendationValidationError:
                            pass
                        else:
                            raise AssertionError(f"{cid}: Agent 4 artifact was not rejected")
                else:
                    artifact_result = RecommendationResult.model_validate(artifact)
                    try:
                        validate_inputs(a3_data, artifact_result)
                    except RecommendationVerificationError:
                        pass
                    else:
                        raise AssertionError(f"{cid}: Agent 5 artifact was not rejected")
                results["negative_stage_validation_passed"] += 1

            results["schema_validation_passed"] += 1

            # 2. Agent 1 -> Agent 2 Dependency Consistency
            a1_deps = a1_data["dependencies"]
            a2_deps = a2_data["dependencies"]
            assert len(a1_deps) == len(a2_deps), f"{cid}: count mismatch A1 vs A2"
            for d1, d2 in zip(a1_deps, a2_deps):
                assert d1["package_name"] == d2["package_name"], f"{cid}: pkg name mismatch"
                assert d1["ecosystem"] == d2["ecosystem"], f"{cid}: ecosystem mismatch"
                assert d1["version_constraint"] == d2["version_constraint"], f"{cid}: version mismatch"
                assert d1["source_file"] == d2["source_file"], f"{cid}: source_file mismatch"
            results["agent1_consistency_passed"] += 1

            # 3. Agent 2 -> Agent 3 Consistency
            a3_deps = a3_data["dependencies"]
            assert len(a2_deps) == len(a3_deps), f"{cid}: count mismatch A2 vs A3"
            for d2, d3 in zip(a2_deps, a3_deps):
                assert d2["package_name"] == d3["package_name"], f"{cid}: pkg name mismatch A2/A3"
                assert d2["status"] == d3["registry_status"], f"{cid}: status mismatch A2/A3"
                if d2["status"] != "not_found":
                    assert d2["status"] != "verified" or d3["risk_level"] == "low"
            results["agent2_consistency_passed"] += 1

            # 4. Agent 3 Reproducibility Check
            cfg = case.get("configuration", {})
            custom_ref = cfg.get("custom_reference_packages")
            custom_pol_dict = cfg.get("custom_risk_policy")
            policy_obj = RiskPolicy(**custom_pol_dict) if custom_pol_dict else None
            reproduced_a3 = analyze_verification(a2_data, reference_packages=custom_ref, policy=policy_obj)
            assert a3_data == reproduced_a3, f"{cid}: Agent 3 reproduction mismatch!"
            results["agent3_reproducibility_passed"] += 1

            # 5. Security Claim Safety (in valid cases)
            if not is_negative:
                for rec in a4_data["recommendations"]:
                    reasoning_lower = rec["reasoning"].lower()
                    for term in FORBIDDEN_TERMS:
                        assert term not in reasoning_lower, f"{cid}: Forbidden security term '{term}' in reasoning: {rec['reasoning']}"
                    # Check suggested_version is null
                    assert rec["suggested_version"] is None, f"{cid}: suggested_version must be null"
                results["security_claim_safety_passed"] += 1

            # 6. Agent 3 -> Agent 4 Evidence Consistency (in valid cases)
            if not is_negative:
                for rec in a4_data["recommendations"]:
                    # Find corresponding A3 dependency
                    matching_a3 = next(d for d in a3_deps if d["package_name"] == rec["package_name"])
                    avail_signal_types = {s["type"] for s in matching_a3["signals"]}
                    for ev in rec["evidence_referenced"]:
                        assert ev in avail_signal_types, f"{cid}: Evidence '{ev}' not in A3 signals: {avail_signal_types}"
                    if rec["action"] == "replace":
                        ref_pkgs = {s.get("reference_package") for s in matching_a3["signals"] if s.get("reference_package")}
                        assert rec["suggested_package"] in ref_pkgs, f"{cid}: Replacement '{rec['suggested_package']}' not in A3 references: {ref_pkgs}"
                results["agent4_evidence_consistency_passed"] += 1

            # 7. Agent 5 and Candidate Remediation Consistency
            crem = case.get("candidate_remediation_ground_truth")
            assert crem is not None, f"{cid}: Missing candidate_remediation_ground_truth"
            if not is_negative:
                if a5_data is not None:
                    # Gating invariants
                    if not a5_data["merge_allowed"]:
                        assert crem["merge_allowed"] is False
                    if a5_data["status"] == "verified":
                        assert a5_data["merge_allowed"] is True
                        assert a5_data["candidate_valid"] is True
                        assert a5_data["tests_available"] is True
                        assert a5_data["tests_passed"] is True
                        assert crem["merge_allowed"] is True
                    elif a5_data["status"] == "rejected":
                        assert a5_data["merge_allowed"] is False
                        assert crem["merge_allowed"] is False
                    elif a5_data["status"] == "requires_review":
                        assert a5_data["merge_allowed"] is False
                        assert crem["merge_allowed"] is False
                results["agent5_validation_passed"] += 1
                results["candidate_remediation_consistency_passed"] += 1
            else:
                # Negative test verification
                assert crem["merge_allowed"] is False
                assert crem["candidate_created"] is False
                results["negative_validation_passed"] += 1

        except Exception as e:
            results["errors"].append(f"{cid} failed: {e}")

    return results


def main():
    ds_file = Path(os.environ.get( "DATASET_PATH",REPO_ROOT/ "research-evaluation-dataset-phase2"/ "research_evaluation_dataset.json", )).expanduser().resolve()
    results = validate_dataset(ds_file)

    print("\n=======================================================")
    print("           EVALUATION DATASET VALIDATION REPORT        ")
    print("=======================================================")
    print(f"Total Cases Evaluated                     : {results['total_cases']}")
    print(f"Valid JSON Syntax                         : {'PASSED' if results['valid_json'] else 'FAILED'}")
    print(f"Schema Validation Passed                  : {results['schema_validation_passed']}/{results['total_cases']}")
    print(f"Agent 1 -> Agent 2 Consistency Passed     : {results['agent1_consistency_passed']}/{results['total_cases']}")
    print(f"Agent 2 -> Agent 3 Consistency Passed     : {results['agent2_consistency_passed']}/{results['total_cases']}")
    print(f"Agent 3 Deterministic Score Reproduction  : {results['agent3_reproducibility_passed']}/{results['total_cases']}")
    print(f"Agent 4 Evidence Consistency Passed       : {results['agent4_evidence_consistency_passed']}/42 (valid cases)")
    print(f"Security Claim Grounding Safety Passed    : {results['security_claim_safety_passed']}/42 (valid cases)")
    print(f"Agent 5 Merge Gate Consistency Passed     : {results['agent5_validation_passed']}/42 (valid cases)")
    print(f"Candidate Remediation Invariants Passed   : {results['candidate_remediation_consistency_passed']}/42 (valid cases)")
    print(f"Negative Case Rejection Invariants           : {results['negative_validation_passed']}/{23}")
    print(f"Negative Rejection Stage Verification         : {results['negative_stage_validation_passed']}/{23}")

    if results["errors"]:
        print(f"\nFAILURES DETECTED ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f" - {err}")
        sys.exit(1)
    else:
        print("\nALL 22 INTERNAL CONSISTENCY CHECKS PASSED PERFECTLY!")
        sys.exit(0)


if __name__ == "__main__":
    main()

