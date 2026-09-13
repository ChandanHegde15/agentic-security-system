
import json

import pytest

from agents.recommendation.agent import RecommendationAgent
from agents.recommendation.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider used for offline Agent 4 tests."""

    def __init__(self, response):
        self.response = response
        self.calls = 0

    def generate(self, *, system_prompt, user_prompt):
        self.calls += 1
        return self.response


@pytest.fixture
def agent3_result():
    """Representative serialized output from Agent 3."""

    return {
        "project_id": "TEST001",
        "dependencies": [
            {
                "package_name": "reqeusts",
                "ecosystem": "pypi",
                "version_constraint": ">=2.30",
                "source_file": "requirements.txt",
                "registry_status": "not_found",
                "risk_score": 90,
                "risk_level": "critical",
                "signals": [
                    {
                        "type": "not_found",
                        "weight": 50,
                        "evidence": (
                            "Package was not found in "
                            "the official pypi registry."
                        ),
                        "reference_package": None,
                        "similarity": None,
                    },
                    {
                        "type": "name_similarity",
                        "weight": 40,
                        "evidence": (
                            "Package name is highly similar "
                            "to reference package."
                        ),
                        "reference_package": "requests",
                        "similarity": 0.95,
                    },
                ],
            }
        ],
    }


def valid_llm_response():
    """Valid structured response that an LLM could return."""

    return json.dumps(
        {
            "project_id": "TEST001",
            "recommendations": [
                {
                    "package_name": "reqeusts",
                    "action": "replace",
                    "suggested_package": "requests",
                    "suggested_version": None,
                    "confidence": 0.9,
                    "reasoning": (
                        "The package is not found in the registry "
                        "and has high name similarity to the supplied "
                        "reference package."
                    ),
                    "evidence_referenced": [
                        "not_found",
                        "name_similarity",
                    ],
                    "conditional": False,
                }
            ],
        }
    )


def test_agent_accepts_valid_llm_response(agent3_result):
    """A valid LLM response should produce RecommendationResult."""

    provider = MockLLMProvider(
        valid_llm_response()
    )

    agent = RecommendationAgent(
        llm_provider=provider
    )

    result = agent.recommend(agent3_result)

    assert result.project_id == "TEST001"
    assert len(result.recommendations) == 1

    recommendation = result.recommendations[0]

    assert recommendation.package_name == "reqeusts"
    assert recommendation.action.value == "replace"
    assert recommendation.suggested_package == "requests"
    assert recommendation.suggested_version is None
    assert recommendation.reasoning == (
        "Recommended action: replace. Agent 3 supplied requests as the "
        "reference-package candidate. Evidence: Package was not found in "
        "the official pypi registry. Package name is highly similar to "
        "reference package."
    )


def test_agent_rebuilds_unsupported_llm_reasoning_from_agent3_evidence(agent3_result):
    response = json.loads(valid_llm_response())
    response["recommendations"][0]["reasoning"] = "This package is malicious."
    agent = RecommendationAgent(llm_provider=MockLLMProvider(json.dumps(response)))

    result = agent.recommend(agent3_result)

    assert "malicious" not in result.recommendations[0].reasoning
    assert result.recommendations[0].reasoning.startswith("Recommended action: replace.")
    assert "Package was not found in the official pypi registry." in result.recommendations[0].reasoning


def test_agent_rejects_invalid_json(agent3_result):
    """Malformed LLM output must be rejected."""

    provider = MockLLMProvider(
        "this is not valid json"
    )

    agent = RecommendationAgent(
        llm_provider=provider
    )

    with pytest.raises(ValueError, match="invalid JSON"):
        agent.recommend(agent3_result)


def test_agent_rejects_invalid_schema(agent3_result):
    """Valid JSON that violates the Agent 4 schema must be rejected."""

    response = json.dumps(
        {
            "project_id": "TEST001",
            "recommendations": [
                {
                    "package_name": "reqeusts",
                    "action": "replace",
                    "suggested_package": "requests"
                }
            ],
        }
    )

    provider = MockLLMProvider(response)

    agent = RecommendationAgent(
        llm_provider=provider
    )

    with pytest.raises(
        ValueError,
        match="does not match Agent 4 recommendation schema",
    ):
        agent.recommend(agent3_result)


def test_agent_rejects_unknown_package(agent3_result):
    """LLM cannot recommend a package absent from Agent 3."""

    response = json.dumps(
        {
            "project_id": "TEST001",
            "recommendations": [
                {
                    "package_name": "unknown_package",
                    "action": "investigate",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Investigate.",
                    "evidence_referenced": [],
                    "conditional": False,
                }
            ],
        }
    )

    provider = MockLLMProvider(response)

    agent = RecommendationAgent(
        llm_provider=provider
    )

    with pytest.raises(
        ValueError,
        match="Unknown package",
    ):
        agent.recommend(agent3_result)


def test_agent_rejects_fake_replacement(agent3_result):
    """LLM cannot invent a replacement package."""

    response = json.dumps(
        {
            "project_id": "TEST001",
            "recommendations": [
                {
                    "package_name": "reqeusts",
                    "action": "replace",
                    "suggested_package": "safe_requests",
                    "suggested_version": None,
                    "confidence": 0.9,
                    "reasoning": "Replace package.",
                    "evidence_referenced": [
                        "not_found"
                    ],
                    "conditional": False,
                }
            ],
        }
    )

    provider = MockLLMProvider(response)

    agent = RecommendationAgent(
        llm_provider=provider
    )

    with pytest.raises(
        ValueError,
        match="Suggested replacement",
    ):
        agent.recommend(agent3_result)


def test_agent_rejects_invented_version(agent3_result):
    """Agent 4 must not invent a replacement version."""

    response = json.dumps(
        {
            "project_id": "TEST001",
            "recommendations": [
                {
                    "package_name": "reqeusts",
                    "action": "replace",
                    "suggested_package": "requests",
                    "suggested_version": "2.32.3",
                    "confidence": 0.9,
                    "reasoning": "Replace package.",
                    "evidence_referenced": [
                        "not_found",
                        "name_similarity",
                    ],
                    "conditional": False,
                }
            ],
        }
    )

    provider = MockLLMProvider(response)

    agent = RecommendationAgent(
        llm_provider=provider
    )

    with pytest.raises(
        ValueError,
        match="Unsupported suggested version",
    ):
        agent.recommend(agent3_result)


def test_agent_rejects_unsupported_evidence(agent3_result):
    """LLM cannot reference evidence absent from Agent 3."""

    response = json.dumps(
        {
            "project_id": "TEST001",
            "recommendations": [
                {
                    "package_name": "reqeusts",
                    "action": "investigate",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Investigate.",
                    "evidence_referenced": [
                        "cve"
                    ],
                    "conditional": False,
                }
            ],
        }
    )

    provider = MockLLMProvider(response)

    agent = RecommendationAgent(
        llm_provider=provider
    )

    with pytest.raises(
        ValueError,
        match="Unsupported evidence",
    ):
        agent.recommend(agent3_result)


def test_agent_rejects_project_id_mismatch(agent3_result):
    """Agent 4 output must belong to the same project."""

    response = json.dumps(
        {
            "project_id": "DIFFERENT_PROJECT",
            "recommendations": [],
        }
    )

    provider = MockLLMProvider(response)

    agent = RecommendationAgent(
        llm_provider=provider
    )

    with pytest.raises(
        ValueError,
        match="Project ID does not match",
    ):
        agent.recommend(agent3_result)


def test_agent_rejects_invalid_agent3_input_before_calling_provider(agent3_result):
    agent3_result["dependencies"][0]["risk_score"] = "90"
    provider = MockLLMProvider(valid_llm_response())
    agent = RecommendationAgent(llm_provider=provider)

    with pytest.raises(ValueError, match="Agent 3 input does not match"):
        agent.recommend(agent3_result)

    assert provider.calls == 0

