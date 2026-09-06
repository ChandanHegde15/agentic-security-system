"""Evidence-based, deterministic risk scoring for Agent 2 results.

Weights and levels are project-defined experimental policy, not a universal
cybersecurity standard. Similarity is a signal whose coverage depends on the
injected reference catalogue; it does not establish maliciousness.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Optional

from agents.registry_verification.models import VerificationRecord, VerificationResult

from .models import RiskRecord, RiskResult, RiskSignal
from .reference_packages import DEFAULT_REFERENCE_PACKAGES
from .similarity import normalized_levenshtein_similarity


# Central experimental scoring policy.
NOT_FOUND_WEIGHT = 50
MODERATE_SIMILARITY_WEIGHT = 20
STRONG_SIMILARITY_WEIGHT = 40
MODERATE_SIMILARITY_THRESHOLD = 0.80
STRONG_SIMILARITY_THRESHOLD = 0.90
LOW_MAX = 19
MEDIUM_MAX = 49
HIGH_MAX = 74


@dataclass(frozen=True)
class RiskPolicy:
    not_found_weight: int = NOT_FOUND_WEIGHT
    moderate_similarity_weight: int = MODERATE_SIMILARITY_WEIGHT
    strong_similarity_weight: int = STRONG_SIMILARITY_WEIGHT
    moderate_similarity_threshold: float = MODERATE_SIMILARITY_THRESHOLD
    strong_similarity_threshold: float = STRONG_SIMILARITY_THRESHOLD
    low_max: int = LOW_MAX
    medium_max: int = MEDIUM_MAX
    high_max: int = HIGH_MAX


def _field(record: VerificationRecord | Mapping[str, Any], name: str) -> Any:
    return getattr(record, name) if isinstance(record, VerificationRecord) else record.get(name)


class RiskAnalyzer:
    """Analyze Agent 2 evidence without making network calls or recommendations."""

    def __init__(
        self,
        reference_packages: Optional[Mapping[str, Iterable[str]]] = None,
        policy: RiskPolicy = RiskPolicy(),
    ) -> None:
        catalogue = DEFAULT_REFERENCE_PACKAGES if reference_packages is None else reference_packages
        self.reference_packages = {
            ecosystem: tuple(package for package in packages if isinstance(package, str))
            for ecosystem, packages in catalogue.items()
        }
        self.policy = policy

    def analyze(self, verification: VerificationResult | Mapping[str, Any]) -> RiskResult:
        if isinstance(verification, VerificationResult):
            project_id, dependencies = verification.project_id, verification.dependencies
        elif isinstance(verification, Mapping):
            project_id, dependencies = verification.get("project_id"), verification.get("dependencies")
            if not isinstance(project_id, str) or not isinstance(dependencies, list):
                return RiskResult("", ())
        else:
            return RiskResult("", ())
        return RiskResult(project_id, tuple(self._analyze_record(record) for record in dependencies))

    def _analyze_record(self, record: Any) -> RiskRecord:
        if not isinstance(record, (VerificationRecord, Mapping)):
            return RiskRecord(None, None, None, None, None, None, "unknown", (
                RiskSignal("invalid_input", 0, "Verification record is not a supported object."),
            ))
        package_name = _field(record, "package_name")
        ecosystem = _field(record, "ecosystem")
        version_constraint = _field(record, "version_constraint")
        source_file = _field(record, "source_file")
        registry_status = _field(record, "status")
        if not all((isinstance(package_name, str), bool(package_name), isinstance(ecosystem, str), isinstance(source_file, str), isinstance(registry_status, str))):
            return RiskRecord(
                package_name if isinstance(package_name, str) else None,
                ecosystem if isinstance(ecosystem, str) else None,
                version_constraint if isinstance(version_constraint, str) else None,
                source_file if isinstance(source_file, str) else None,
                registry_status if isinstance(registry_status, str) else None,
                None,
                "unknown",
                (RiskSignal("invalid_input", 0, "Verification record has missing or invalid required fields."),),
            )
        if version_constraint is not None and not isinstance(version_constraint, str):
            return RiskRecord(package_name, ecosystem, None, source_file, "invalid_input", None, "unknown", (
                RiskSignal("invalid_input", 0, "Verification record has an invalid version constraint."),
            ))
        if registry_status != "not_found":
            return self._unknown_or_verified(package_name, ecosystem, version_constraint, source_file, registry_status)

        signals = [RiskSignal(
            "not_found", self.policy.not_found_weight,
            f"Package was not found in the official {ecosystem} registry.",
        )]
        similarity_signal = self._similarity_signal(package_name, ecosystem)
        if similarity_signal is not None:
            signals.append(similarity_signal)
        score = min(100, sum(signal.weight for signal in signals))
        return RiskRecord(package_name, ecosystem, version_constraint, source_file, registry_status, score, self.risk_level(score), tuple(signals))

    def _unknown_or_verified(self, package_name: str, ecosystem: str, version_constraint: Optional[str], source_file: str, status: str) -> RiskRecord:
        if status == "verified":
            return RiskRecord(package_name, ecosystem, version_constraint, source_file, status, 0, "low", ())
        evidence = {
            "registry_error": "Registry verification was unavailable; risk cannot be calculated.",
            "unsupported_ecosystem": "The ecosystem is unsupported; risk cannot be calculated.",
            "invalid_input": "Verification input was invalid; risk cannot be calculated.",
        }.get(status, "Verification status is invalid or unavailable; risk cannot be calculated.")
        signal_type = status if status in {"registry_error", "unsupported_ecosystem", "invalid_input"} else "invalid_input"
        return RiskRecord(package_name, ecosystem, version_constraint, source_file, status, None, "unknown", (RiskSignal(signal_type, 0, evidence),))

    def _similarity_signal(self, package_name: str, ecosystem: str) -> Optional[RiskSignal]:
        references = self.reference_packages.get(ecosystem, ())
        if not package_name or not references:
            return None
        reference, similarity = max(
            ((reference, normalized_levenshtein_similarity(package_name, reference)) for reference in references),
            key=lambda pair: pair[1],
        )
        if similarity >= self.policy.strong_similarity_threshold:
            weight, evidence = self.policy.strong_similarity_weight, "Package name has high similarity to a reference package."
        elif similarity >= self.policy.moderate_similarity_threshold:
            weight, evidence = self.policy.moderate_similarity_weight, "Package name has moderate similarity to a reference package."
        else:
            return None
        return RiskSignal("name_similarity", weight, evidence, reference, similarity)

    def risk_level(self, score: int) -> str:
        if score <= self.policy.low_max:
            return "low"
        if score <= self.policy.medium_max:
            return "medium"
        if score <= self.policy.high_max:
            return "high"
        return "critical"


def analyze_verification(
    verification: VerificationResult | Mapping[str, Any],
    *,
    reference_packages: Optional[Mapping[str, Iterable[str]]] = None,
    policy: Optional[RiskPolicy] = None,
) -> dict[str, Any]:
    """Return Agent 3's serialized analysis with optional experiment settings."""
    return RiskAnalyzer(
        reference_packages=reference_packages,
        policy=RiskPolicy() if policy is None else policy,
    ).analyze(verification).to_dict()
