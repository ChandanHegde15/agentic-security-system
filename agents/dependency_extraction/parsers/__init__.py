"""Manifest parsers for supported dependency ecosystems."""

from .package_json_parser import PackageJsonParseError, parse_package_json
from .requirements_parser import RequirementsParseError, parse_requirements

__all__ = [
    "PackageJsonParseError",
    "RequirementsParseError",
    "parse_package_json",
    "parse_requirements",
]
