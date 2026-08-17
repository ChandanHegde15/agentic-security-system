"""Data models used by the dependency extraction agent."""

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class Dependency:
    package_name: str
    ecosystem: str
    version_constraint: Optional[str]
    source_file: str

    def to_dict(self) -> dict[str, Optional[str]]:
        return asdict(self)


@dataclass(frozen=True)
class ExtractionResult:
    project_id: str
    dependencies: tuple[Dependency, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "dependencies": [dependency.to_dict() for dependency in self.dependencies],
        }
