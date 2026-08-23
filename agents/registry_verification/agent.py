"""Public entry points for Agent 2: Registry Verification."""

from collections.abc import Mapping
from typing import Any

from agents.dependency_extraction.models import ExtractionResult

from .models import VerificationResult
from .verifier import verify_dependencies


def verify_extraction(extraction: ExtractionResult | Mapping[str, Any], **clients: Any) -> dict[str, Any]:
    """Verify the serialized or model-layer output of Agent 1."""
    if isinstance(extraction, ExtractionResult):
        result = verify_dependencies(extraction.project_id, extraction.dependencies, **clients)
    elif isinstance(extraction, Mapping):
        project_id = extraction.get("project_id")
        dependencies = extraction.get("dependencies")
        if not isinstance(project_id, str) or not isinstance(dependencies, list):
            return VerificationResult("", ()).to_dict()
        result = verify_dependencies(project_id, dependencies, **clients)
    else:
        return VerificationResult("", ()).to_dict()
    return result.to_dict()
