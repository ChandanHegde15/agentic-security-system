from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

class RecommendationAction(str, Enum):
    NO_ACTION='no_action'; MONITOR='monitor'; INVESTIGATE='investigate'; REPLACE='replace'; REVIEW='review'; INSUFFICIENT_EVIDENCE='insufficient_evidence'

class Recommendation(BaseModel):
    model_config=ConfigDict(extra='forbid')
    package_name:str=Field(min_length=1)
    action:RecommendationAction
    suggested_package:Optional[str]=None
    suggested_version:Optional[str]=None
    confidence:float=Field(ge=0.0,le=1.0)
    reasoning:str=Field(min_length=1)
    evidence_referenced:list[str]=Field(default_factory=list)
    conditional:bool

class RecommendationResult(BaseModel):
    model_config=ConfigDict(extra='forbid')
    project_id:str=Field(min_length=1)
    recommendations:list[Recommendation]


class Agent3Signal(BaseModel):
    """Strict local mirror of a serialized Agent 3 signal."""

    model_config = ConfigDict(extra="forbid", strict=True)
    type: str = Field(min_length=1)
    weight: int
    evidence: str = Field(min_length=1)
    reference_package: Optional[str] = None
    similarity: Optional[float] = None


class Agent3Dependency(BaseModel):
    """Strict local mirror of a serialized Agent 3 dependency record."""

    model_config = ConfigDict(extra="forbid", strict=True)
    package_name: Optional[str]
    ecosystem: Optional[str]
    version_constraint: Optional[str]
    source_file: Optional[str]
    registry_status: Optional[
        Literal[
            "verified",
            "not_found",
            "registry_error",
            "unsupported_ecosystem",
            "invalid_input",
        ]
    ]
    risk_score: Optional[int] = Field(default=None, ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical", "unknown"]
    signals: list[Agent3Signal]

    @model_validator(mode="after")
    def validate_unknown_risk_state(self) -> "Agent3Dependency":
        if (self.risk_score is None) != (self.risk_level == "unknown"):
            raise ValueError("risk_score and risk_level have an inconsistent unknown state")
        return self


class Agent3RiskResult(BaseModel):
    """Strict local mirror of Agent 3's public serialized result."""

    model_config = ConfigDict(extra="forbid", strict=True)
    project_id: str = Field(min_length=1)
    dependencies: list[Agent3Dependency]
