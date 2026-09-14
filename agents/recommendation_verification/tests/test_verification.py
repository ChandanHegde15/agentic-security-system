import json
import subprocess
from pathlib import Path

import pytest

from agents.recommendation_verification.agent import RecommendationVerifier
from agents.recommendation_verification.models import VerificationStatus
from agents.recommendation_verification.validation import (
    RecommendationVerificationError,
    validate_inputs,
)


def dependency(name, *, status="not_found", risk_level="critical", signals=None, source_file="requirements.txt"):
    if signals is None:
        signals = [
            {"type": "not_found", "weight": 50, "evidence": "Package was not found."},
            {
                "type": "name_similarity",
                "weight": 40,
                "evidence": "Package name is similar to a reference package.",
                "reference_package": "requests",
                "similarity": 0.95,
            },
        ]
    return {
        "package_name": name,
        "ecosystem": "pypi",
        "version_constraint": None,
        "source_file": source_file,
        "registry_status": status,
        "risk_score": None if risk_level == "unknown" else 90,
        "risk_level": risk_level,
        "signals": signals,
    }


def recommendation(name, action, *, evidence=None, suggested_package=None, conditional=False, reasoning=None):
    if evidence is None:
        evidence = []
    if reasoning is None:
        signal_evidence = {
            "not_found": "Package was not found.",
            "name_similarity": "Package name is similar to a reference package.",
            "registry_error": "Registry verification was unavailable.",
        }
        joined = " ".join(signal_evidence.get(item, "Unsupported evidence.") for item in evidence)
        prefix = f"Recommended action: {action}."
        if action == "replace":
            reasoning = f"{prefix} Agent 3 supplied {suggested_package} as the reference-package candidate. Evidence: {joined}"
        elif joined:
            reasoning = f"{prefix} Evidence: {joined}"
        else:
            reasoning = f"{prefix} No Agent 3 signals were referenced for this recommendation."
    return {
        "package_name": name,
        "action": action,
        "suggested_package": suggested_package,
        "suggested_version": None,
        "confidence": 0.8,
        "reasoning": reasoning,
        "evidence_referenced": evidence,
        "conditional": conditional,
    }


def inputs(recommendations, dependencies=None):
    dependencies = dependencies or [dependency("reqeusts")]
    return (
        {"project_id": "P100", "dependencies": dependencies},
        {"project_id": "P100", "recommendations": recommendations},
    )


@pytest.mark.parametrize(
    ("action", "evidence", "conditional"),
    [
        ("no_action", [], False),
        ("monitor", ["not_found"], False),
        ("investigate", ["not_found"], False),
        ("review", ["not_found"], False),
    ],
)
def test_valid_nonreplacement_actions(action, evidence, conditional):
    agent3, agent4 = inputs([recommendation("reqeusts", action, evidence=evidence, conditional=conditional)])
    _, parsed = validate_inputs(agent3, agent4)
    assert parsed.recommendations[0].action.value == action


def test_valid_replace_requires_authoritative_reference():
    agent3, agent4 = inputs([recommendation("reqeusts", "replace", evidence=["not_found", "name_similarity"], suggested_package="requests")])
    validate_inputs(agent3, agent4)


def test_valid_insufficient_evidence_for_unknown_state():
    unknown = dependency(
        "uncertain",
        status="registry_error",
        risk_level="unknown",
        signals=[{"type": "registry_error", "weight": 0, "evidence": "Registry verification was unavailable."}],
    )
    agent3, agent4 = inputs([recommendation("uncertain", "insufficient_evidence", evidence=["registry_error"], conditional=True)], [unknown])
    validate_inputs(agent3, agent4)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda result: result.update(project_id="other"),
        lambda result: result["recommendations"].append(recommendation("reqeusts", "review", evidence=["not_found"])),
        lambda result: result["recommendations"].__setitem__(0, recommendation("unknown", "review")),
        lambda result: result["recommendations"][0].update(action="unsupported"),
    ],
)
def test_rejects_invalid_recommendation_structure(mutate):
    agent3, agent4 = inputs([recommendation("reqeusts", "review", evidence=["not_found"])])
    mutate(agent4)
    with pytest.raises(RecommendationVerificationError):
        validate_inputs(agent3, agent4)


def test_rejects_missing_coverage_wrong_evidence_and_ungrounded_reasoning():
    agent3, agent4 = inputs([], [dependency("one"), dependency("two")])
    with pytest.raises(RecommendationVerificationError, match="coverage"):
        validate_inputs(agent3, agent4)

    agent3, agent4 = inputs([recommendation("reqeusts", "review", evidence=["other_signal"])])
    with pytest.raises(RecommendationVerificationError, match="unsupported evidence"):
        validate_inputs(agent3, agent4)

    agent3, agent4 = inputs([recommendation("reqeusts", "review", evidence=["not_found"], reasoning="The package is malicious.")])
    with pytest.raises(RecommendationVerificationError, match="not grounded"):
        validate_inputs(agent3, agent4)


def test_reasoning_wording_variation_is_accepted_but_unsupported_claims_are_rejected():
    agent3, agent4 = inputs([
        recommendation(
            "reqeusts",
            "investigate",
            evidence=["not_found"],
            reasoning="Package was not found in the registry, so investigation is recommended.",
        )
    ])
    validate_inputs(agent3, agent4)

    for claim in (
        "Package was found in registry, so investigation is recommended.",
        "The package exists in the official registry.",
        "This package is malware.",
        "This package is compromised.",
        "This is intentional typo-squatting.",
    ):
        agent3, agent4 = inputs([
            recommendation("reqeusts", "investigate", evidence=["not_found"], reasoning=claim)
        ])
        with pytest.raises(RecommendationVerificationError, match="not grounded"):
            validate_inputs(agent3, agent4)


def test_rejects_fake_replacement_invented_version_and_unknown_state_overclaim():
    agent3, agent4 = inputs([recommendation("reqeusts", "replace", evidence=["not_found", "name_similarity"], suggested_package="fake")])
    with pytest.raises(RecommendationVerificationError, match="not backed"):
        validate_inputs(agent3, agent4)

    agent3, agent4 = inputs([recommendation("reqeusts", "replace", evidence=["not_found", "name_similarity"], suggested_package="requests")])
    agent4["recommendations"][0]["suggested_version"] = "1.0.0"
    with pytest.raises(RecommendationVerificationError, match="versions"):
        validate_inputs(agent3, agent4)

    unknown = dependency("uncertain", status="registry_error", risk_level="unknown", signals=[{"type": "registry_error", "weight": 0, "evidence": "Registry verification was unavailable."}])
    agent3, agent4 = inputs([recommendation("uncertain", "investigate", evidence=["registry_error"], conditional=False)], [unknown])
    with pytest.raises(RecommendationVerificationError, match="Unknown Agent 3"):
        validate_inputs(agent3, agent4)


def create_repository(path: Path, *, include_tests: bool = True) -> None:
    def git(*args):
        subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True)
    git("init", "-b", "main")
    git("config", "user.email", "agent5@example.invalid")
    git("config", "user.name", "Agent 5 Test")
    (path / "requirements.txt").write_text("reqeusts\n", encoding="utf-8")
    if include_tests:
        (path / "test_candidate.py").write_text("def test_candidate():\n    assert True\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "base")


def runner_without_installs(command, cwd):
    if command[0] == "git":
        return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return subprocess.CompletedProcess(command, 0, "", "")


def runner_with_failure(failing_fragment):
    def runner(command, cwd):
        if command[0] == "git":
            return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
        if failing_fragment in command:
            return subprocess.CompletedProcess(command, 1, "", "simulated failure")
        return subprocess.CompletedProcess(command, 0, "", "")
    return runner


def test_candidate_branch_isolated_and_success_authorizes_merge(tmp_path):
    create_repository(tmp_path)
    agent3, agent4 = inputs([recommendation("reqeusts", "replace", evidence=["not_found", "name_similarity"], suggested_package="requests")])

    result = RecommendationVerifier(runner_without_installs).verify(agent3, agent4, tmp_path)

    assert result.status is VerificationStatus.VERIFIED
    assert result.merge_allowed is True
    assert (tmp_path / "requirements.txt").read_text(encoding="utf-8") == "reqeusts\n"
    branch_content = subprocess.run(["git", "show", f"{result.branch_name}:requirements.txt"], cwd=tmp_path, capture_output=True, text=True, check=True).stdout
    assert branch_content == "requests\n"
    assert subprocess.run(["git", "branch", "--show-current"], cwd=tmp_path, capture_output=True, text=True, check=True).stdout.strip() == "main"


def test_failed_candidate_blocks_merge_and_branch_collision_fails_closed(tmp_path):
    create_repository(tmp_path)
    agent3, agent4 = inputs([recommendation("reqeusts", "replace", evidence=["not_found", "name_similarity"], suggested_package="requests")])
    verifier = RecommendationVerifier(runner_without_installs)
    branch_name = verifier._branch_name("P100", validate_inputs(agent3, agent4)[1])
    subprocess.run(["git", "branch", branch_name], cwd=tmp_path, check=True, capture_output=True, text=True)

    result = verifier.verify(agent3, agent4, tmp_path)

    assert result.status is VerificationStatus.REQUIRES_REVIEW
    assert result.merge_allowed is False


def test_install_failure_test_failure_and_missing_tests_block_merge(tmp_path):
    agent3, agent4 = inputs([recommendation("reqeusts", "replace", evidence=["not_found", "name_similarity"], suggested_package="requests")])

    install_repository = tmp_path / "install"
    install_repository.mkdir()
    create_repository(install_repository)
    install_result = RecommendationVerifier(runner_with_failure("pip")).verify(agent3, agent4, install_repository)
    assert install_result.status is VerificationStatus.REJECTED
    assert install_result.merge_allowed is False

    tests_repository = tmp_path / "tests"
    tests_repository.mkdir()
    create_repository(tests_repository)
    test_result = RecommendationVerifier(runner_with_failure("pytest")).verify(agent3, agent4, tests_repository)
    assert test_result.status is VerificationStatus.REJECTED
    assert test_result.tests_available is True
    assert test_result.tests_passed is False

    no_tests_repository = tmp_path / "no-tests"
    no_tests_repository.mkdir()
    create_repository(no_tests_repository, include_tests=False)
    no_tests_result = RecommendationVerifier(runner_without_installs).verify(agent3, agent4, no_tests_repository)
    assert no_tests_result.status is VerificationStatus.REQUIRES_REVIEW
    assert no_tests_result.tests_available is False
    assert no_tests_result.merge_allowed is False


def test_underscore_suffix_test_and_tests_directory_are_detected(tmp_path):
    verifier = RecommendationVerifier(runner_without_installs)
    python = tmp_path / "python"
    (tmp_path / "candidate_test.py").write_text("", encoding="utf-8")
    assert verifier._run_project_tests(tmp_path, python) == (True, True)

    (tmp_path / "candidate_test.py").unlink()
    (tmp_path / "tests").mkdir()
    assert verifier._run_project_tests(tmp_path, python) == (True, True)
