
import pytest

from agents.recommendation.models import (
    Recommendation,
    RecommendationAction,
    RecommendationResult,
)
from agents.recommendation.validation import (
    Agent3InputValidationError,
    RecommendationValidationError,
    validate_agent3_input,
    validate_recommendation,
)


@pytest.fixture
def agent3_result():
    """Representative Agent 3 output."""
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


def make_result(
    package_name="reqeusts",
    action=RecommendationAction.REPLACE,
    suggested_package="requests",
    suggested_version=None,
    evidence_referenced=None,
    project_id="TEST001",
):
    """Create an Agent 4 recommendation result for testing."""

    if evidence_referenced is None:
        evidence_referenced = [
            "not_found",
            "name_similarity",
        ]

    recommendation = Recommendation(
        package_name=package_name,
        action=action,
        suggested_package=suggested_package,
        suggested_version=suggested_version,
        confidence=0.9,
        reasoning="Recommendation based only on Agent 3 evidence.",
        evidence_referenced=evidence_referenced,
        conditional=False,
    )

    return RecommendationResult(
        project_id=project_id,
        recommendations=[recommendation],
    )


def test_valid_recommendation(agent3_result):
    """A valid recommendation should pass validation."""

    result = make_result()

    validated = validate_recommendation(
        result,
        agent3_result,
    )

    assert validated.project_id == result.project_id
    assert validated.recommendations[0].reasoning == (
        "Recommended action: replace. Agent 3 supplied requests as the "
        "reference-package candidate. Evidence: Package was not found in "
        "the official pypi registry. Package name is highly similar to "
        "reference package."
    )


def test_unknown_package_is_rejected(agent3_result):
    """Agent 4 must not recommend a package absent from Agent 3."""

    result = make_result(
        package_name="unknown_package",
    )

    with pytest.raises(RecommendationValidationError):
        validate_recommendation(
            result,
            agent3_result,
        )


def test_unsupported_evidence_is_rejected(agent3_result):
    """Agent 4 must not reference evidence absent from Agent 3."""

    result = make_result(
        evidence_referenced=[
            "not_found",
            "cve",
        ],
    )

    with pytest.raises(RecommendationValidationError):
        validate_recommendation(
            result,
            agent3_result,
        )


def test_fake_replacement_package_is_rejected(agent3_result):
    """Replacement must come from Agent 3 reference_package."""

    result = make_result(
        suggested_package="malicious_package",
    )

    with pytest.raises(RecommendationValidationError):
        validate_recommendation(
            result,
            agent3_result,
        )


def test_invented_version_is_rejected(agent3_result):
    """Agent 4 must not invent a replacement version."""

    result = make_result(
        suggested_version="2.32.3",
    )

    with pytest.raises(RecommendationValidationError):
        validate_recommendation(
            result,
            agent3_result,
        )


def test_project_id_mismatch_is_rejected(agent3_result):
    """Agent 4 output must belong to the same project."""

    result = make_result(
        project_id="DIFFERENT_PROJECT",
    )

    with pytest.raises(RecommendationValidationError):
        validate_recommendation(
            result,
            agent3_result,
        )


def test_replace_without_package_is_rejected(agent3_result):
    """Replace action requires a suggested package."""

    result = make_result(
        action=RecommendationAction.REPLACE,
        suggested_package=None,
    )

    with pytest.raises(RecommendationValidationError):
        validate_recommendation(
            result,
            agent3_result,
        )


def test_no_action_without_replacement_is_valid(agent3_result):
    """A no_action recommendation does not require a replacement."""

    result = make_result(
        action=RecommendationAction.NO_ACTION,
        suggested_package=None,
        evidence_referenced=[],
    )

    validated = validate_recommendation(
        result,
        agent3_result,
    )

    assert validated.recommendations[0].reasoning == (
        "Recommended action: no_action. No Agent 3 signals were referenced "
        "for this recommendation."
    )


def test_agent3_input_schema_rejects_unexpected_or_inconsistent_values(agent3_result):
    agent3_result["dependencies"][0]["unexpected"] = True
    with pytest.raises(Agent3InputValidationError):
        validate_agent3_input(agent3_result)

    agent3_result["dependencies"][0].pop("unexpected")
    agent3_result["dependencies"][0]["risk_score"] = None
    agent3_result["dependencies"][0]["risk_level"] = "critical"
    with pytest.raises(Agent3InputValidationError):
        validate_agent3_input(agent3_result)

