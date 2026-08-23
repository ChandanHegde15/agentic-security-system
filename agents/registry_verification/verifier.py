"""Dependency validation and registry-client orchestration."""

from collections.abc import Iterable, Mapping
from typing import Any

from agents.dependency_extraction.models import Dependency

from .models import VerificationRecord, VerificationResult
from .registries import NpmClient, PyPIClient
from .registries.pypi_client import RegistryClientError


def _read_field(dependency: Dependency | Mapping[str, Any], name: str) -> Any:
    return getattr(dependency, name) if isinstance(dependency, Dependency) else dependency.get(name)


def verify_dependencies(
    project_id: str,
    dependencies: Iterable[Dependency | Mapping[str, Any]],
    *,
    pypi_client: PyPIClient | None = None,
    npm_client: NpmClient | None = None,
) -> VerificationResult:
    """Verify each Agent 1 dependency independently against its official registry."""
    pypi_client = pypi_client or PyPIClient()
    npm_client = npm_client or NpmClient()
    records: list[VerificationRecord] = []

    for dependency in dependencies:
        if not isinstance(dependency, (Dependency, Mapping)):
            records.append(VerificationRecord(None, None, None, None, None, "invalid_input", None))
            continue
        package_name = _read_field(dependency, "package_name")
        ecosystem = _read_field(dependency, "ecosystem")
        version_constraint = _read_field(dependency, "version_constraint")
        source_file = _read_field(dependency, "source_file")
        if not isinstance(package_name, str) or not package_name or not isinstance(ecosystem, str):
            records.append(VerificationRecord(package_name if isinstance(package_name, str) else None, ecosystem if isinstance(ecosystem, str) else None, version_constraint if isinstance(version_constraint, str) else None, source_file if isinstance(source_file, str) else None, None, "invalid_input", None))
            continue
        if (
            (version_constraint is not None and not isinstance(version_constraint, str))
            or not isinstance(source_file, str)
        ):
            records.append(VerificationRecord(package_name, ecosystem, None, source_file if isinstance(source_file, str) else None, None, "invalid_input", None))
            continue
        client = {"pypi": pypi_client, "npm": npm_client}.get(ecosystem)
        if client is None:
            records.append(VerificationRecord(package_name, ecosystem, version_constraint, source_file, None, "unsupported_ecosystem", None))
            continue
        try:
            metadata = client.get_package_metadata(package_name)
        except RegistryClientError:
            records.append(VerificationRecord(package_name, ecosystem, version_constraint, source_file, None, "registry_error", None))
        else:
            records.append(VerificationRecord(package_name, ecosystem, version_constraint, source_file, metadata is not None, "verified" if metadata else "not_found", metadata))
    return VerificationResult(project_id=project_id, dependencies=tuple(records))
