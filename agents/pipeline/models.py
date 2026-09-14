"""Serialized result model for the end-to-end security pipeline."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PipelineResult:
    """Preserves each agent's native output and exposes Agent 5's merge gate."""

    project_id: str
    extraction: dict[str, Any]
    verification: dict[str, Any]
    risk_analysis: dict[str, Any]
    recommendations: dict[str, Any]
    recommendation_verification: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "extraction": self.extraction,
            "verification": self.verification,
            "risk_analysis": self.risk_analysis,
            "recommendations": self.recommendations,
            "recommendation_verification": self.recommendation_verification,
            "merge_allowed": self.recommendation_verification["merge_allowed"],
        }
