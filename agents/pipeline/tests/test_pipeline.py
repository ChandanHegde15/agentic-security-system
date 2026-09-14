"""Offline integration coverage for the runtime pipeline."""

import json
import subprocess
from pathlib import Path

import pytest

from agents.pipeline import run_pipeline
from agents.recommendation.llm.base import LLMProvider
from agents.recommendation_verification import RecommendationVerifier


class NotFoundPyPIClient:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def get_package_metadata(self, package_name: str):
        self.events.append(f"registry:{package_name}")
        return None


class MockProvider(LLMProvider):
    def __init__(self, response: dict[str, object], events: list[str]) -> None:
        self._response = response
        self._events = events
        self.risk_input: dict[str, object] | None = None

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.risk_input = json.loads(user_prompt)
        self._events.append("agent4")
        return json.dumps(self._response)


class RecordingVerifier(RecommendationVerifier):
    def __init__(self, events: list[str], runner) -> None:
        super().__init__(runner)
        self._events = events
        self.agent3_input = None
        self.agent4_input = None

    def verify(self, agent3_result, recommendation_result, project_directory):
        self._events.append("agent5")
        self.agent3_input = agent3_result
        self.agent4_input = recommendation_result
        return super().verify(agent3_result, recommendation_result, project_directory)


def _create_project(path: Path) -> None:
    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True)

    git("init", "-b", "main")
    git("config", "user.email", "pipeline@example.invalid")
    git("config", "user.name", "Pipeline Test")
    (path / "requirements.txt").write_text("request\n", encoding="utf-8")
    (path / "test_project.py").write_text("def test_project():\n    assert True\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "base")


def _runner(*, fail_tests: bool = False):
    def run(command: list[str], cwd: Path):
        if command[0] == "git":
            return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
        if fail_tests and "pytest" in command:
            return subprocess.CompletedProcess(command, 1, "", "simulated test failure")
        return subprocess.CompletedProcess(command, 0, "", "")

    return run


def _response(*, suggested_package: str = "requests", action: str = "replace") -> dict[str, object]:
    return {
        "project_id": "project",
        "recommendations": [{
            "package_name": "request",
            "action": action,
            "suggested_package": suggested_package if action == "replace" else None,
            "suggested_version": None,
            "confidence": 0.9,
            "reasoning": "LLM-provided wording is replaced with Agent 3 evidence.",
            "evidence_referenced": ["not_found", "name_similarity"] if action == "replace" else ["not_found"],
            "conditional": False,
        }],
    }


def test_pipeline_runs_all_agents_in_order_and_preserves_agent3_evidence(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    _create_project(project)
    events: list[str] = []
    provider = MockProvider(_response(), events)
    verifier = RecordingVerifier(events, _runner())

    result = run_pipeline(
        project, llm_provider=provider, pypi_client=NotFoundPyPIClient(events),
        recommendation_verifier=verifier,
    )

    assert events == ["registry:request", "agent4", "agent5"]
    assert provider.risk_input == result["risk_analysis"]
    assert verifier.agent3_input == result["risk_analysis"]
    assert verifier.agent4_input.model_dump(mode="json") == result["recommendations"]
    assert result["recommendation_verification"]["merge_allowed"] is True
    assert result["merge_allowed"] is True
    assert (project / "requirements.txt").read_text(encoding="utf-8") == "request\n"
    assert subprocess.run(["git", "branch", "--show-current"], cwd=project, check=True, capture_output=True, text=True).stdout.strip() == "main"


def test_pipeline_exposes_failed_candidate_validation_without_merging(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    _create_project(project)
    events: list[str] = []
    result = run_pipeline(
        project, llm_provider=MockProvider(_response(), events),
        pypi_client=NotFoundPyPIClient(events),
        recommendation_verifier=RecordingVerifier(events, _runner(fail_tests=True)),
    )

    assert result["recommendation_verification"]["status"] == "rejected"
    assert result["recommendation_verification"]["merge_allowed"] is False
    assert result["merge_allowed"] is False
    assert (project / "requirements.txt").read_text(encoding="utf-8") == "request\n"


@pytest.mark.parametrize(
    ("response", "expected_events"),
    [
        (_response(suggested_package="invented-replacement"), ["registry:request", "agent4"]),
        (
            {**_response(), "recommendations": [{**_response()["recommendations"][0], "evidence_referenced": ["not_found"]}]},
            ["registry:request", "agent4", "agent5"],
        ),
    ],
)
def test_pipeline_blocks_unsupported_or_contradictory_agent4_recommendations(tmp_path, response, expected_events):
    project = tmp_path / "project"
    project.mkdir()
    _create_project(project)
    events: list[str] = []
    verifier = RecordingVerifier(events, _runner())

    with pytest.raises(ValueError):
        run_pipeline(
            project, llm_provider=MockProvider(response, events),
            pypi_client=NotFoundPyPIClient(events), recommendation_verifier=verifier,
        )

    assert events == expected_events
