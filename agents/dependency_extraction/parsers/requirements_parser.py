"""Parser for the supported, name-based subset of requirements.txt."""

import re
from pathlib import Path

from ..models import Dependency


class RequirementsParseError(ValueError):
    """Raised when a requirements.txt declaration is unsupported or malformed."""


_REQUIREMENT_PATTERN = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"(?:\[[A-Za-z0-9._,-]+\])?"
    r"\s*(?P<constraint>(?:(?:===|==|!=|<=|>=|~=|<|>)\s*[^\s,;]+"
    r"(?:\s*,\s*(?:===|==|!=|<=|>=|~=|<|>)\s*[^\s,;]+)*))?\s*$"
)


def parse_requirements(path: Path) -> list[Dependency]:
    """Extract direct named requirements from *path* without resolving them.

    Blank lines and comment-only lines are ignored. Exact repeated declarations
    are emitted once, preserving the first declaration's order.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as error:
        raise RequirementsParseError(f"Unable to read {path}: {error}") from error
    except UnicodeDecodeError as error:
        raise RequirementsParseError(f"Unable to decode {path} as UTF-8") from error

    dependencies: list[Dependency] = []
    seen: set[tuple[str, str | None]] = set()
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        declaration = raw_line.split("#", maxsplit=1)[0].strip()
        if not declaration:
            continue

        match = _REQUIREMENT_PATTERN.fullmatch(declaration)
        if not match:
            raise RequirementsParseError(
                f"Malformed or unsupported requirement in {path} at line {line_number}: "
                f"{raw_line!r}"
            )

        package_name = match.group("name")
        constraint = match.group("constraint")
        version_constraint = re.sub(r"\s+", "", constraint) if constraint else None
        identity = (package_name.lower(), version_constraint)
        if identity in seen:
            continue
        seen.add(identity)
        dependencies.append(
            Dependency(package_name, "pypi", version_constraint, path.name)
        )
    return dependencies
