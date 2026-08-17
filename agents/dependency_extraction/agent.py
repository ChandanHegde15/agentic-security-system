"""Public entry point for Agent 1: Dependency Extraction."""

from pathlib import Path

from .models import ExtractionResult
from .scanner import scan_project


def extract_dependencies(project_directory: str | Path) -> dict[str, object]:
    """Return the standardized dependency extraction structure for a project."""
    return scan_project(project_directory).to_dict()
