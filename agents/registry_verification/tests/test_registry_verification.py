import json
import socket
import unittest
from urllib.error import HTTPError, URLError

from agents.dependency_extraction.models import Dependency, ExtractionResult
from agents.registry_verification.agent import verify_extraction
from agents.registry_verification.registries import NpmClient, PyPIClient
from agents.registry_verification.registries.pypi_client import RegistryClientError
from agents.registry_verification.verifier import verify_dependencies


class FakeResponse:
    def __init__(self, payload: object, status: int = 200) -> None:
        self.status = status
        self._body = json.dumps(payload).encode("utf-8") if not isinstance(payload, bytes) else payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self._body


def opener_for(response: FakeResponse):
    def opener(url: str, timeout: float):
        return response
    return opener


class StubClient:
    def __init__(self, outcomes: dict[str, object]) -> None:
        self.outcomes = outcomes

    def get_package_metadata(self, package_name: str):
        outcome = self.outcomes[package_name]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class RegistryClientTests(unittest.TestCase):
    def test_pypi_found_and_metadata_extraction(self) -> None:
        client = PyPIClient(opener_for(FakeResponse({"info": {"name": "requests", "version": "2.32.0"}})))
        self.assertEqual(client.get_package_metadata("requests"), {"name": "requests", "version": "2.32.0"})

    def test_npm_found_and_metadata_extraction(self) -> None:
        client = NpmClient(opener_for(FakeResponse({"name": "express", "dist-tags": {"latest": "5.0.0"}})))
        self.assertEqual(client.get_package_metadata("express"), {"name": "express", "version": "5.0.0"})

    def test_pypi_and_npm_404_are_not_found(self) -> None:
        def not_found(url: str, timeout: float):
            raise HTTPError(url, 404, "Not Found", None, None)

        self.assertIsNone(PyPIClient(not_found).get_package_metadata("missing"))
        self.assertIsNone(NpmClient(not_found).get_package_metadata("missing"))

    def test_timeout_connection_unexpected_status_and_malformed_response_are_errors(self) -> None:
        def timeout(url: str, timeout: float):
            raise socket.timeout("timed out")

        def connection_error(url: str, timeout: float):
            raise URLError("offline")

        for client in (
            PyPIClient(timeout),
            NpmClient(connection_error),
            PyPIClient(opener_for(FakeResponse({}, status=503))),
            NpmClient(opener_for(FakeResponse(b"not-json"))),
        ):
            with self.subTest(client=client.__class__.__name__):
                with self.assertRaises(RegistryClientError):
                    client.get_package_metadata("package")


class VerificationTests(unittest.TestCase):
    def test_version_constraint_preserved_and_verified(self) -> None:
        result = verify_dependencies(
            "P001",
            [Dependency("requests", "pypi", ">=2.30", "requirements.txt")],
            pypi_client=StubClient({"requests": {"name": "requests", "version": "2.32.0"}}),
        ).to_dict()
        record = result["dependencies"][0]
        self.assertEqual(record["version_constraint"], ">=2.30")
        self.assertEqual(record["status"], "verified")
        self.assertTrue(record["exists"])
        self.assertEqual(record["registry_metadata"], {"name": "requests", "version": "2.32.0"})

    def test_unsupported_and_invalid_input(self) -> None:
        result = verify_dependencies(
            "P001",
            [
                {"package_name": "crate", "ecosystem": "cargo", "version_constraint": None, "source_file": "Cargo.toml"},
                {"ecosystem": "pypi", "source_file": "requirements.txt"},
            ],
        ).to_dict()
        self.assertEqual([record["status"] for record in result["dependencies"]], ["unsupported_ecosystem", "invalid_input"])
        self.assertEqual([record["exists"] for record in result["dependencies"]], [None, None])

    def test_multiple_dependencies_continue_after_registry_error(self) -> None:
        result = verify_dependencies(
            "P008",
            [
                Dependency("pandas", "pypi", None, "requirements.txt"),
                Dependency("missing", "pypi", None, "requirements.txt"),
                Dependency("express", "npm", "^5.0.0", "package.json"),
            ],
            pypi_client=StubClient({
                "pandas": {"name": "pandas", "version": "2.2.0"},
                "missing": RegistryClientError("unavailable"),
            }),
            npm_client=StubClient({"express": None}),
        ).to_dict()
        self.assertEqual([record["status"] for record in result["dependencies"]], ["verified", "registry_error", "not_found"])
        self.assertEqual([record["exists"] for record in result["dependencies"]], [True, None, False])

    def test_accepts_agent_one_model_and_serialized_output(self) -> None:
        extraction = ExtractionResult("P005", (Dependency("express", "npm", "^5.0.0", "package.json"),))
        client = StubClient({"express": {"name": "express", "version": "5.0.0"}})
        model_result = verify_extraction(extraction, npm_client=client)
        serialized_result = verify_extraction(extraction.to_dict(), npm_client=client)
        self.assertEqual(model_result, serialized_result)
        self.assertEqual(model_result["project_id"], "P005")
        self.assertEqual(model_result["dependencies"][0]["source_file"], "package.json")


if __name__ == "__main__":
    unittest.main()
