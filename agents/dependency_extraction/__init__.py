"""Deterministic extraction of declared Python and npm dependencies."""

from .agent import extract_dependencies
from .models import Dependency, ExtractionResult

__all__ = ["Dependency", "ExtractionResult", "extract_dependencies"]
