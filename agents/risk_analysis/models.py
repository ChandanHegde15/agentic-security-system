"""Models emitted by the deterministic risk-analysis agent."""

from dataclasses import asdict, dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class RiskSignal:
    type: str
    weight: int
    evidence: str
    reference_package: Optional[str] = None
    similarity: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass(frozen=True)
class RiskRecord:
    package_name: Optional[str]
    ecosystem: Optional[str]
    version_constraint: Optional[str]
    source_file: Optional[str]
    registry_status: Optional[str]
    risk_score: Optional[int]
    risk_level: str
    signals: tuple[RiskSignal, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["signals"] = [signal.to_dict() for signal in self.signals]
        return data


@dataclass(frozen=True)
class RiskResult:
    project_id: str
    dependencies: tuple[RiskRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "dependencies": [dependency.to_dict() for dependency in self.dependencies],
        }
