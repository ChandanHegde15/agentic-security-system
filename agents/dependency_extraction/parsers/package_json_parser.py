"""Parser for runtime dependencies declared in package.json."""

import json
from pathlib import Path

from ..models import Dependency


class PackageJsonParseError(ValueError):
    """Raised when package.json cannot be safely parsed for dependencies."""


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PackageJsonParseError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def parse_package_json(path: Path) -> list[Dependency]:
    """Extract runtime dependencies only; devDependencies are deliberately ignored."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as error:
        raise PackageJsonParseError(f"Unable to read {path}: {error}") from error
    except UnicodeDecodeError as error:
        raise PackageJsonParseError(f"Unable to decode {path} as UTF-8") from error

    try:
        manifest = json.loads(content, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as error:
        raise PackageJsonParseError(
            f"Malformed JSON in {path} at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error

    if not isinstance(manifest, dict):
        raise PackageJsonParseError(f"Top-level JSON value in {path} must be an object")

    declared = manifest.get("dependencies", {})
    if declared is None:
        return []
    if not isinstance(declared, dict):
        raise PackageJsonParseError(f"'dependencies' in {path} must be an object")

    dependencies: list[Dependency] = []
    for package_name, version_constraint in declared.items():
        if not isinstance(package_name, str) or not package_name:
            raise PackageJsonParseError(f"Dependency name in {path} must be a non-empty string")
        if not isinstance(version_constraint, str):
            raise PackageJsonParseError(
                f"Version constraint for {package_name!r} in {path} must be a string"
            )
        dependencies.append(
            Dependency(
                package_name=package_name,
                ecosystem="npm",
                version_constraint=version_constraint or None,
                source_file=path.name,
            )
        )
    return dependencies
