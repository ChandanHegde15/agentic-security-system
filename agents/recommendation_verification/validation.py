"""Independent validation of Agent 4 recommendations against Agent 3 evidence."""

from collections.abc import Mapping
import re
from typing import Any

from pydantic import ValidationError

from agents.recommendation.models import (
    Agent3Dependency,
    Agent3RiskResult,
    Recommendation,
    RecommendationAction,
    RecommendationResult,
)


class RecommendationVerificationError(ValueError):
    """Raised for malformed or unsupported upstream recommendations."""


_NEUTRAL_ACTION_CLAUSES = {
    "no action",
    "monitor",
    "monitoring is recommended",
    "investigate",
    "investigation is recommended",
    "further investigation is recommended",
    "replace",
    "replacement is recommended",
    "review",
    "review is recommended",
    "insufficient evidence",
    "no agent 3 signals were referenced for this recommendation",
}


def _normalise_clause(clause: str) -> str:
    clause = clause.casefold().replace("_", " ").replace("-", " ")
    clause = re.sub(r"\s+", " ", clause).strip(" ,:;.")
    for prefix in ("recommended action: ", "evidence: ", "because "):
        if clause.startswith(prefix):
            clause = clause[len(prefix):]
    return clause


def _matches_signal_clause(signal_type: str, clause: str) -> bool:
    patterns = {
        "not_found": r"(?:the )?package (?:(?:was )?not found|could not be found)(?: in (?:the )?(?:official )?(?:[a-z]+ )?registry)?",
        "name_similarity": r"package name (?:is|has) (?:high |moderate )?(?:similar|similarity)(?: to)? (?:a |the )?reference package",
        "registry_error": r"registry verification (?:was |is )?unavailable",
        "unsupported_ecosystem": r"(?:the )?ecosystem (?:was |is )?unsupported",
        "invalid_input": r"verification input (?:was |is )?invalid",
    }
    pattern = patterns.get(signal_type)
    return pattern is not None and re.fullmatch(pattern, clause) is not None


def _reasoning_is_grounded(recommendation: Recommendation, dependency: Agent3Dependency) -> bool:
    """Validate factual clauses against referenced Agent 3 signal meanings."""
    signals = [
        signal
        for signal in dependency.signals
        if signal.type in recommendation.evidence_referenced
    ]
    clauses = [
        _normalise_clause(clause)
        for clause in re.split(r"[.;]|,\s*(?:so|because)\s+", recommendation.reasoning)
        if _normalise_clause(clause)
    ]
    seen_signal_types: set[str] = set()
    for clause in clauses:
        if clause in _NEUTRAL_ACTION_CLAUSES:
            continue
        if recommendation.action is RecommendationAction.REPLACE:
            reference = re.escape(recommendation.suggested_package or "")
            if re.fullmatch(rf"agent 3 supplied {reference} as (?:the )?reference package candidate", clause):
                continue
        matching_signal_types = {
            signal.type
            for signal in signals
            if _matches_signal_clause(signal.type, clause)
        }
        if not matching_signal_types:
            return False
        seen_signal_types.update(matching_signal_types)
    return {signal.type for signal in signals}.issubset(seen_signal_types)


def validate_inputs(
    agent3_result: Mapping[str, Any],
    recommendation_result: RecommendationResult | Mapping[str, Any],
) -> tuple[Agent3RiskResult, RecommendationResult]:
    """Validate coverage, evidence, replacement, and reasoning grounding."""
    try:
        risk_result = Agent3RiskResult.model_validate(agent3_result)
        recommendations = (
            recommendation_result
            if isinstance(recommendation_result, RecommendationResult)
            else RecommendationResult.model_validate(recommendation_result)
        )
    except ValidationError as error:
        raise RecommendationVerificationError("Upstream input does not match its expected schema.") from error

    if risk_result.project_id != recommendations.project_id:
        raise RecommendationVerificationError("Agent 3 and Agent 4 project IDs do not match.")

    dependencies = {dependency.package_name: dependency for dependency in risk_result.dependencies}
    if None in dependencies or "" in dependencies:
        raise RecommendationVerificationError("Agent 3 contains a dependency without a package name.")
    recommendation_names = [recommendation.package_name for recommendation in recommendations.recommendations]
    if len(recommendation_names) != len(set(recommendation_names)):
        raise RecommendationVerificationError("Duplicate recommendations are not allowed.")
    if set(recommendation_names) != set(dependencies):
        missing = sorted(set(dependencies) - set(recommendation_names))
        unknown = sorted(set(recommendation_names) - set(dependencies))
        raise RecommendationVerificationError(
            f"Recommendation coverage does not match Agent 3 dependencies; missing={missing}, unknown={unknown}."
        )

    for recommendation in recommendations.recommendations:
        dependency = dependencies[recommendation.package_name]
        signal_types = {signal.type for signal in dependency.signals}
        unsupported_evidence = set(recommendation.evidence_referenced) - signal_types
        if unsupported_evidence:
            raise RecommendationVerificationError(
                f"Recommendation for {recommendation.package_name} cites unsupported evidence: "
                f"{sorted(unsupported_evidence)}."
            )
        reference_packages = {
            signal.reference_package
            for signal in dependency.signals
            if signal.reference_package is not None
        }
        if recommendation.action is RecommendationAction.REPLACE:
            if "name_similarity" not in recommendation.evidence_referenced:
                raise RecommendationVerificationError("Replacement requires referenced name_similarity evidence.")
            if recommendation.suggested_package not in reference_packages:
                raise RecommendationVerificationError("Replacement package is not backed by Agent 3 evidence.")
        elif recommendation.suggested_package is not None:
            raise RecommendationVerificationError("Only replacement recommendations may suggest a package.")
        if recommendation.suggested_version is not None:
            raise RecommendationVerificationError("Suggested versions are not authoritative in the current Agent 3 contract.")

        unknown_state = dependency.risk_level == "unknown" or any(
            signal.type in {"registry_error", "unsupported_ecosystem", "invalid_input"}
            for signal in dependency.signals
        )
        if unknown_state and (
            recommendation.action not in {
                RecommendationAction.REVIEW,
                RecommendationAction.INSUFFICIENT_EVIDENCE,
            }
            or not recommendation.conditional
        ):
            raise RecommendationVerificationError(
                "Unknown Agent 3 states require a conditional review or insufficient_evidence recommendation."
            )
        if not _reasoning_is_grounded(recommendation, dependency):
            raise RecommendationVerificationError(
                f"Recommendation reasoning for {recommendation.package_name} is not grounded in Agent 3 evidence."
            )
    return risk_result, recommendations
