import json
import tempfile
import unittest
from pathlib import Path

from agents.dependency_extraction.agent import extract_dependencies
from agents.dependency_extraction.parsers.package_json_parser import PackageJsonParseError
from agents.dependency_extraction.parsers.requirements_parser import RequirementsParseError
from agents.dependency_extraction.scanner import scan_project


def dependency_names(result: dict[str, object]) -> list[str]:
    return [item["package_name"] for item in result["dependencies"]]  # type: ignore[index]


class DependencyExtractionUnitTests(unittest.TestCase):
    def create_project(self, files: dict[str, str]) -> Path:
        temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temp_directory.cleanup)
        project = Path(temp_directory.name) / "PX01"
        project.mkdir()
        for name, content in files.items():
            (project / name).write_text(content, encoding="utf-8")
        return project

    def test_requirements_basic_extraction(self) -> None:
        project = self.create_project({"requirements.txt": "pandas\nnumpy\nrequests\n"})

        result = extract_dependencies(project)

        self.assertEqual(result["project_id"], "PX01")
        self.assertEqual(dependency_names(result), ["pandas", "numpy", "requests"])
        self.assertTrue(all(item["ecosystem"] == "pypi" for item in result["dependencies"]))  # type: ignore[index]
        self.assertTrue(all(item["version_constraint"] is None for item in result["dependencies"]))  # type: ignore[index]

    def test_requirements_version_constraints(self) -> None:
        project = self.create_project(
            {"requirements.txt": "requests>=2.30\nnumpy==2.0.0\nflask~=3.0\n"}
        )

        result = extract_dependencies(project)

        self.assertEqual(
            [(item["package_name"], item["version_constraint"]) for item in result["dependencies"]],  # type: ignore[index]
            [("requests", ">=2.30"), ("numpy", "==2.0.0"), ("flask", "~=3.0")],
        )

    def test_package_json_extraction_and_version_constraints(self) -> None:
        project = self.create_project(
            {
                "package.json": json.dumps(
                    {
                        "dependencies": {
                            "express": "^5.0.0",
                            "axios": "~1.2.3",
                            "library": ">=1.0.0",
                        },
                        "devDependencies": {"jest": "^29.0.0"},
                    }
                )
            }
        )

        result = extract_dependencies(project)

        self.assertEqual(
            [(item["package_name"], item["version_constraint"]) for item in result["dependencies"]],  # type: ignore[index]
            [("express", "^5.0.0"), ("axios", "~1.2.3"), ("library", ">=1.0.0")],
        )
        self.assertTrue(all(item["ecosystem"] == "npm" for item in result["dependencies"]))  # type: ignore[index]

    def test_suspicious_looking_names_are_extracted_without_classification(self) -> None:
        project = self.create_project(
            {
                "requirements.txt": "superfast-ai-99999\nreqeusts\n",
                "package.json": '{"dependencies":{"super-ai-package-99999":"^1.0.0","expres":"^5.0.0"}}',
            }
        )

        result = extract_dependencies(project)

        self.assertEqual(
            dependency_names(result),
            ["superfast-ai-99999", "reqeusts", "super-ai-package-99999", "expres"],
        )

    def test_mixed_ecosystem_project(self) -> None:
        project = self.create_project(
            {
                "requirements.txt": "pandas\n",
                "package.json": '{"dependencies":{"express":"^5.0.0"}}',
            }
        )

        result = extract_dependencies(project)

        self.assertEqual(dependency_names(result), ["pandas", "express"])
        self.assertEqual(
            [item["source_file"] for item in result["dependencies"]],  # type: ignore[index]
            ["requirements.txt", "package.json"],
        )

    def test_malformed_inputs_raise_clear_errors(self) -> None:
        malformed_requirements = self.create_project({"requirements.txt": "requests="})
        malformed_json = self.create_project({"package.json": "{not json}"})

        with self.assertRaises(RequirementsParseError):
            extract_dependencies(malformed_requirements)
        with self.assertRaises(PackageJsonParseError):
            extract_dependencies(malformed_json)

    def test_missing_or_empty_dependency_files_return_empty_dependencies(self) -> None:
        missing = self.create_project({"README.md": "no manifests"})
        empty = self.create_project({"requirements.txt": "\n# comment\n", "package.json": "{}"})

        self.assertEqual(extract_dependencies(missing), {"project_id": "PX01", "dependencies": []})
        self.assertEqual(extract_dependencies(empty), {"project_id": "PX01", "dependencies": []})

    def test_duplicate_requirements_are_deduplicated_and_duplicate_json_keys_fail(self) -> None:
        project = self.create_project({"requirements.txt": "pandas\npandas\nnumpy==2.0\nnumpy==2.0\n"})
        duplicate_keys = self.create_project(
            {"package.json": '{"dependencies":{"express":"^5.0.0","express":"^4.0.0"}}'}
        )

        self.assertEqual(dependency_names(extract_dependencies(project)), ["pandas", "numpy"])
        with self.assertRaises(PackageJsonParseError):
            extract_dependencies(duplicate_keys)


class DependencyExtractionIntegrationTests(unittest.TestCase):
    PROJECTS_DIRECTORY = Path(__file__).resolve().parents[3] / "test-projects"

    def test_controlled_projects_p001_to_p008(self) -> None:
        expected = {
            "P001": ["pandas", "numpy", "requests", "flask"],
            "P002": ["pandas", "numpy", "requests", "flask"],
            "P003": ["pandas", "numpy", "superfast-ai-99999"],
            "P004": ["pandas", "reqeusts"],
            "P005": ["express", "axios"],
            "P006": ["express", "super-ai-package-99999"],
            "P007": ["express", "expres"],
            "P008": ["pandas", "numpy", "requests", "express", "axios"],
        }
        for project_id, expected_names in expected.items():
            with self.subTest(project_id=project_id):
                result = extract_dependencies(self.PROJECTS_DIRECTORY / project_id)
                self.assertEqual(result["project_id"], project_id)
                self.assertEqual(dependency_names(result), expected_names)

    def test_p002_constraints_and_p008_sources(self) -> None:
        p002 = extract_dependencies(self.PROJECTS_DIRECTORY / "P002")
        p008 = extract_dependencies(self.PROJECTS_DIRECTORY / "P008")

        self.assertEqual(
            [item["version_constraint"] for item in p002["dependencies"]],  # type: ignore[index]
            [">=2.0", "==2.0.0", ">=2.30", None],
        )
        self.assertEqual(
            [item["source_file"] for item in p008["dependencies"]],  # type: ignore[index]
            ["requirements.txt", "requirements.txt", "requirements.txt", "package.json", "package.json"],
        )


if __name__ == "__main__":
    unittest.main()
