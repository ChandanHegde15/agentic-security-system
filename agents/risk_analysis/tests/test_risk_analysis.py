import socket
import unittest
from unittest.mock import patch

from agents.dependency_extraction.agent import extract_dependencies
from agents.registry_verification.agent import verify_extraction
from agents.registry_verification.models import VerificationRecord, VerificationResult
from agents.registry_verification.registries.pypi_client import RegistryClientError
from agents.risk_analysis.analyzer import RiskAnalyzer, RiskPolicy, analyze_verification
from agents.risk_analysis.similarity import levenshtein_distance, normalized_levenshtein_similarity


def verification_record(name: str, ecosystem: str, status: str, version: str | None = None) -> dict[str, object]:
    return {
        "package_name": name,
        "ecosystem": ecosystem,
        "version_constraint": version,
        "source_file": "requirements.txt" if ecosystem == "pypi" else "package.json",
        "exists": status == "verified",
        "status": status,
        "registry_metadata": None,
    }


class StubPyPIClient:
    def get_package_metadata(self, package_name: str):
        if package_name == "superfast-ai-99999":
            return None
        if package_name == "unavailable":
            raise RegistryClientError("offline")
        return {"name": package_name, "version": "1.0.0"}


class RiskAnalysisTests(unittest.TestCase):
    def test_public_api_accepts_custom_catalogue_and_policy_without_changing_defaults(self) -> None:
        verification = {"project_id": "P", "dependencies": [
            verification_record("abcxef", "pypi", "not_found"),
        ]}
        default_result = analyze_verification(verification)
        explicit_default_result = analyze_verification(
            verification,
            reference_packages=None,
            policy=None,
        )
        custom_result = analyze_verification(
            verification,
            reference_packages={"pypi": ("abcdef",)},
            policy=RiskPolicy(not_found_weight=60, moderate_similarity_weight=25),
        )
        self.assertEqual(default_result, explicit_default_result)
        self.assertEqual(default_result["dependencies"][0]["risk_score"], 50)
        self.assertEqual(custom_result["dependencies"][0]["risk_score"], 85)
        self.assertEqual(custom_result["dependencies"][0]["signals"][1]["reference_package"], "abcdef")

    def test_verified_pypi_and_npm_are_low_without_similarity_signals(self) -> None:
        result = analyze_verification({"project_id": "P001", "dependencies": [
            verification_record("requests", "pypi", "verified", ">=2.30"),
            verification_record("express", "npm", "verified", "^5.0.0"),
        ]})
        self.assertEqual([(record["risk_score"], record["risk_level"], record["signals"]) for record in result["dependencies"]], [(0, "low", []), (0, "low", [])])

    def test_not_found_without_similarity_is_high(self) -> None:
        analyzer = RiskAnalyzer({"pypi": ("unrelated",), "npm": ()})
        result = analyzer.analyze({"project_id": "P003", "dependencies": [verification_record("abc", "pypi", "not_found")]}).to_dict()
        record = result["dependencies"][0]
        self.assertEqual((record["risk_score"], record["risk_level"]), (50, "high"))
        self.assertEqual(record["signals"][0]["weight"], 50)

    def test_not_found_moderate_and_strong_similarity(self) -> None:
        moderate = RiskAnalyzer({"pypi": ("abcdef",)}).analyze({"project_id": "P", "dependencies": [verification_record("abcxef", "pypi", "not_found")]}).to_dict()["dependencies"][0]
        strong = RiskAnalyzer({"pypi": ("abcdefghij",)}).analyze({"project_id": "P", "dependencies": [verification_record("abcdefghiX", "pypi", "not_found")]}).to_dict()["dependencies"][0]
        self.assertEqual((moderate["risk_score"], moderate["risk_level"], moderate["signals"][1]["weight"]), (70, "high", 20))
        self.assertEqual((strong["risk_score"], strong["risk_level"], strong["signals"][1]["weight"]), (90, "critical", 40))
        self.assertAlmostEqual(moderate["signals"][1]["similarity"], 5 / 6)
        self.assertAlmostEqual(strong["signals"][1]["similarity"], 0.9)

    def test_levenshtein_math_case_and_empty_names(self) -> None:
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)
        self.assertAlmostEqual(normalized_levenshtein_similarity("kitten", "sitting"), 4 / 7)
        self.assertEqual(normalized_levenshtein_similarity("Requests", "requests"), 1.0)
        self.assertEqual(normalized_levenshtein_similarity("", ""), 1.0)
        self.assertEqual(normalized_levenshtein_similarity("", "abc"), 0.0)

    def test_similarity_is_ecosystem_specific_and_injected_catalogue_is_used(self) -> None:
        analyzer = RiskAnalyzer({"pypi": ("only-pypi",), "npm": ()})
        result = analyzer.analyze({"project_id": "P", "dependencies": [
            verification_record("only-pypi", "npm", "not_found"),
            verification_record("only-pypi", "pypi", "not_found"),
        ]}).to_dict()
        self.assertEqual([record["risk_score"] for record in result["dependencies"]], [50, 90])
        self.assertEqual(len(result["dependencies"][0]["signals"]), 1)
        self.assertEqual(result["dependencies"][1]["signals"][1]["reference_package"], "only-pypi")

    def test_unknown_statuses_never_become_not_found(self) -> None:
        result = analyze_verification({"project_id": "P", "dependencies": [
            verification_record("unavailable", "pypi", "registry_error"),
            verification_record("crate", "cargo", "unsupported_ecosystem"),
            verification_record("", "pypi", "invalid_input"),
        ]})
        self.assertEqual([(record["risk_score"], record["risk_level"]) for record in result["dependencies"]], [(None, "unknown"), (None, "unknown"), (None, "unknown")])
        self.assertEqual([record["signals"][0]["type"] for record in result["dependencies"]], ["registry_error", "unsupported_ecosystem", "invalid_input"])

    def test_score_cap_levels_and_signals_reconstruct_score(self) -> None:
        analyzer = RiskAnalyzer(
            {"pypi": ("abcdefghij",)},
            RiskPolicy(not_found_weight=90, strong_similarity_weight=40),
        )
        record = analyzer.analyze({"project_id": "P", "dependencies": [verification_record("abcdefghiX", "pypi", "not_found")]}).to_dict()["dependencies"][0]
        self.assertEqual(record["risk_score"], 100)
        self.assertEqual(sum(signal["weight"] for signal in record["signals"]), 130)
        self.assertEqual(record["risk_level"], "critical")
        levels = RiskAnalyzer()
        self.assertEqual([levels.risk_level(value) for value in (0, 19, 20, 49, 50, 74, 75, 100)], ["low", "low", "medium", "medium", "high", "high", "critical", "critical"])

    def test_metadata_project_and_multiple_dependencies_are_preserved(self) -> None:
        result = analyze_verification({"project_id": "P008", "dependencies": [
            verification_record("missing", "pypi", "not_found", ">=1.0"),
            verification_record("express", "npm", "verified", "^5.0.0"),
        ]})
        self.assertEqual(result["project_id"], "P008")
        self.assertEqual([(item["version_constraint"], item["source_file"]) for item in result["dependencies"]], [(">=1.0", "requirements.txt"), ("^5.0.0", "package.json")])
        self.assertEqual([item["risk_score"] for item in result["dependencies"]], [50, 0])

    def test_model_layer_input_and_empty_package_name_are_safe(self) -> None:
        model = VerificationResult("P", (VerificationRecord("", "pypi", None, "requirements.txt", None, "invalid_input", None),))
        result = RiskAnalyzer().analyze(model).to_dict()
        self.assertEqual(result["dependencies"][0]["risk_level"], "unknown")
        self.assertEqual(result["dependencies"][0]["signals"][0]["type"], "invalid_input")

    def test_agent_three_does_not_make_network_requests(self) -> None:
        with patch("urllib.request.urlopen", side_effect=socket.timeout("network used")):
            result = analyze_verification({"project_id": "P", "dependencies": [verification_record("missing", "pypi", "not_found")]})
        self.assertEqual(result["dependencies"][0]["risk_score"], 50)


class AgentTwoToThreeIntegrationTests(unittest.TestCase):
    def test_serialized_agent_two_output_flows_directly_to_agent_three(self) -> None:
        extraction = extract_dependencies("test-projects/P003")
        verification = verify_extraction(extraction, pypi_client=StubPyPIClient())
        analysis = analyze_verification(verification)
        self.assertEqual(analysis["project_id"], "P003")
        self.assertEqual([item["package_name"] for item in analysis["dependencies"]], ["pandas", "numpy", "superfast-ai-99999"])
        self.assertEqual(analysis["dependencies"][-1]["registry_status"], "not_found")
        self.assertEqual(analysis["dependencies"][-1]["risk_score"], 50)


if __name__ == "__main__":
    unittest.main()
