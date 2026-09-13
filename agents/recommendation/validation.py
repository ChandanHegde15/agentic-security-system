from typing import Any

from pydantic import ValidationError

from .models import Agent3RiskResult, Recommendation, RecommendationResult
class RecommendationValidationError(ValueError): pass
class Agent3InputValidationError(ValueError): pass


def validate_agent3_input(agent3_input: dict[str, Any]) -> Agent3RiskResult:
    """Validate Agent 3's existing serialized contract before LLM invocation."""
    try:
        return Agent3RiskResult.model_validate(agent3_input)
    except ValidationError as error:
        raise Agent3InputValidationError("Agent 3 input does not match the expected schema.") from error


def _evidence_grounded_reasoning(recommendation: Recommendation, signals: list[dict[str, Any]]) -> str:
    """Construct output reasoning only from validated Agent 3 evidence."""
    evidence = " ".join(signal["evidence"] for signal in signals)
    action = f"Recommended action: {recommendation.action.value}."
    if not evidence:
        return f"{action} No Agent 3 signals were referenced for this recommendation."
    if recommendation.action.value == "replace":
        return (
            f"{action} Agent 3 supplied {recommendation.suggested_package} as the "
            f"reference-package candidate. Evidence: {evidence}"
        )
    return f"{action} Evidence: {evidence}"

def validate_recommendation(result:RecommendationResult, agent3_input:dict[str,Any])->RecommendationResult:
    deps=agent3_input.get('dependencies',[]); evidence_by={}; refs_by={}; signals_by={}
    for d in deps:
        name=d.get('package_name')
        if not name: continue
        signals = [s for s in (d.get('signals') or []) if s.get('type')]
        evidence_by[name]={s['type'] for s in signals}
        refs_by[name]={s.get('reference_package') for s in signals if s.get('reference_package')}
        signals_by[name] = signals
    if result.project_id != agent3_input.get('project_id'): raise RecommendationValidationError('Project ID does not match Agent 3 input.')
    validated_recommendations = []
    for r in result.recommendations:
        if r.package_name not in evidence_by: raise RecommendationValidationError(f'Unknown package in recommendation: {r.package_name}')
        unsupported=set(r.evidence_referenced)-evidence_by[r.package_name]
        if unsupported: raise RecommendationValidationError(f'Unsupported evidence for {r.package_name}: {sorted(unsupported)}')
        if r.action.value=='replace':
            if not r.suggested_package: raise RecommendationValidationError(f'Replacement action for {r.package_name} requires suggested_package.')
            if r.suggested_package not in refs_by[r.package_name]: raise RecommendationValidationError(f'Suggested replacement {r.suggested_package} was not supplied as a reference package by Agent 3.')
        if r.suggested_version is not None: raise RecommendationValidationError(f'Unsupported suggested version for {r.package_name}: {r.suggested_version}')
        referenced_signals = [
            signal for signal in signals_by[r.package_name]
            if signal['type'] in r.evidence_referenced
        ]
        validated_recommendations.append(r.model_copy(update={
            'reasoning': _evidence_grounded_reasoning(r, referenced_signals),
        }))
    return RecommendationResult(
        project_id=result.project_id,
        recommendations=validated_recommendations,
    )
