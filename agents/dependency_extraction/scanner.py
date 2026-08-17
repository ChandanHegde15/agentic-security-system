"""Project-level manifest discovery and parser orchestration."""

from pathlib import Path

from .models import Dependency, ExtractionResult
from .parsers import parse_package_json, parse_requirements


def scan_project(project_directory: str | Path) -> ExtractionResult:
    """Scan supported manifests directly inside a project directory.

    A directory without supported manifests is valid and produces an empty
    dependency list. Malformed or unreadable manifests raise parser errors.
    """
    project_path = Path(project_directory)
    if not project_path.exists():
        raise FileNotFoundError(f"Project directory does not exist: {project_path}")
    if not project_path.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {project_path}")

    dependencies: list[Dependency] = []
    requirements_file = project_path / "requirements.txt"
    package_json_file = project_path / "package.json"

    if requirements_file.exists():
        if not requirements_file.is_file():
            raise IsADirectoryError(f"Expected a file: {requirements_file}")
        dependencies.extend(parse_requirements(requirements_file))
    if package_json_file.exists():
        if not package_json_file.is_file():
            raise IsADirectoryError(f"Expected a file: {package_json_file}")
        dependencies.extend(parse_package_json(package_json_file))

    return ExtractionResult(project_id=project_path.name, dependencies=tuple(dependencies))
