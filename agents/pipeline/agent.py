"""Minimal runtime composition of Agents 1 through 5."""

from pathlib import Path
from typing import Any

from agents.dependency_extraction import extract_dependencies
from agents.recommendation import RecommendationAgent
from agents.recommendation_verification import RecommendationVerifier, verify_recommendations
from agents.registry_verification import verify_extraction
from agents.risk_analysis import analyze_verification

from .models import PipelineResult


def run_pipeline(
    project_directory: str | Path,
    *,
    llm_provider: Any,
    pypi_client: Any = None,
    npm_client: Any = None,
    recommendation_verifier: RecommendationVerifier | None = None,
) -> dict[str, Any]:
    """Run the existing agents in order and return their serialized outputs.

    Registry clients, the LLM provider, and Agent 5's verifier are injectable
    so callers can run deterministic offline tests. Agent 5 alone owns
    candidate-remediation validation and never merges the resulting branch.
    """
    extraction = extract_dependencies(project_directory)
    registry_clients = {
        name: client
        for name, client in (("pypi_client", pypi_client), ("npm_client", npm_client))
        if client is not None
    }
    verification = verify_extraction(extraction, **registry_clients)
    risk_analysis = analyze_verification(verification)
    recommendations = RecommendationAgent(llm_provider=llm_provider).recommend(risk_analysis)
    if recommendation_verifier is None:
        recommendation_verification = verify_recommendations(
            risk_analysis, recommendations, project_directory
        )
    else:
        recommendation_verification = recommendation_verifier.verify(
            risk_analysis, recommendations, project_directory
        )
    return PipelineResult(
        project_id=extraction["project_id"],
        extraction=extraction,
        verification=verification,
        risk_analysis=risk_analysis,
        recommendations=recommendations.model_dump(mode="json"),
        recommendation_verification=recommendation_verification.model_dump(mode="json"),
    ).to_dict()
