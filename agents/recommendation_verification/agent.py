"""Isolated candidate remediation and merge authorization for Agent 5."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from agents.recommendation.models import RecommendationAction, RecommendationResult

from .models import VerificationResult, VerificationStatus
from .validation import RecommendationVerificationError, validate_inputs


CommandRunner = Callable[[list[str], Path], subprocess.CompletedProcess[str]]


def _run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)


class RecommendationVerifier:
    """Verify supported Python replacement candidates in a Git worktree.

    The current upstream contract has no authoritative replacement version.
    npm candidates therefore fail closed; requirements.txt candidates can be
    tested as an unpinned, isolated candidate without modifying the source tree.
    """

    def __init__(self, command_runner: CommandRunner = _run_command) -> None:
        self._run = command_runner

    def verify(
        self,
        agent3_result: Mapping[str, Any],
        recommendation_result: RecommendationResult | Mapping[str, Any],
        project_directory: str | Path,
    ) -> VerificationResult:
        risk_result, recommendations = validate_inputs(agent3_result, recommendation_result)
        replacements = [
            recommendation
            for recommendation in recommendations.recommendations
            if recommendation.action is RecommendationAction.REPLACE
        ]
        if not replacements:
            return self._result(
                risk_result.project_id, None, VerificationStatus.REQUIRES_REVIEW, False, None, False,
                False,
                ["No replacement candidate was supplied for isolated remediation verification."],
            )
        project_path = Path(project_directory).resolve()
        if not project_path.is_dir():
            return self._result(
                risk_result.project_id, None, VerificationStatus.REJECTED, False, None, False,
                False,
                [f"Project directory does not exist: {project_path}"],
            )
        try:
            repository = self._repository_root(project_path)
        except RecommendationVerificationError as error:
            return self._result(risk_result.project_id, None, VerificationStatus.REJECTED, False, None, False, False, [str(error)])

        dependencies = {dependency.package_name: dependency for dependency in risk_result.dependencies}
        unsupported = [
            recommendation.package_name
            for recommendation in replacements
            if dependencies[recommendation.package_name].source_file != "requirements.txt"
        ]
        if unsupported:
            return self._result(
                risk_result.project_id, None, VerificationStatus.REQUIRES_REVIEW, False, None, False,
                False,
                ["Isolated remediation currently supports requirements.txt replacements only; " f"unsupported={unsupported}."],
            )

        branch_name = self._branch_name(risk_result.project_id, recommendations)
        if self._branch_exists(repository, branch_name):
            return self._result(
                risk_result.project_id, branch_name, VerificationStatus.REQUIRES_REVIEW, False, None, False,
                False,
                ["Verification branch already exists; Agent 5 will not overwrite it."],
            )
        return self._verify_python_candidate(repository, branch_name, risk_result.project_id, replacements, dependencies)

    def _verify_python_candidate(self, repository: Path, branch_name: str, project_id: str, replacements: list[Any], dependencies: dict[str, Any]) -> VerificationResult:
        with tempfile.TemporaryDirectory(prefix="agent5-worktree-") as worktree_directory, tempfile.TemporaryDirectory(prefix="agent5-venv-") as environment_directory:
            worktree = Path(worktree_directory) / "candidate"
            try:
                self._require(["git", "worktree", "add", "-b", branch_name, str(worktree), "HEAD"], repository)
                changed_files = set()
                for recommendation in replacements:
                    source_file = worktree / dependencies[recommendation.package_name].source_file
                    self._apply_requirement_replacement(source_file, recommendation.package_name, recommendation.suggested_package)
                    changed_files.add(source_file.relative_to(worktree).as_posix())
                modified_files = self._modified_files(worktree)
                if modified_files != changed_files:
                    raise RecommendationVerificationError(
                        f"Candidate contains unexpected modifications: {sorted(modified_files - changed_files)}."
                    )
                environment = Path(environment_directory)
                self._require([sys.executable, "-m", "venv", str(environment)], worktree)
                python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
                self._require([str(python), "-m", "pip", "install", "-r", str(worktree / "requirements.txt")], worktree)
                tests_available, tests_passed = self._run_project_tests(worktree, python)
                if not tests_available:
                    return self._result(project_id, branch_name, VerificationStatus.REQUIRES_REVIEW, False, None, False, False, ["No project test suite was detected; merge is not authorized."])
                if not tests_passed:
                    return self._result(project_id, branch_name, VerificationStatus.REJECTED, True, False, False, False, ["Candidate project tests failed."])
                self._require(["git", "add", "--", *sorted(changed_files)], worktree)
                self._require(["git", "commit", "-m", f"Agent 5 verified remediation for {project_id}"], worktree)
                return self._result(project_id, branch_name, VerificationStatus.VERIFIED, True, True, True, True, ["Candidate remediation was applied in an isolated verification branch and project tests passed."])
            except RecommendationVerificationError as error:
                return self._result(project_id, branch_name, VerificationStatus.REJECTED, False, None, False, False, [str(error)])
            finally:
                self._run(["git", "worktree", "remove", "--force", str(worktree)], repository)

    def _repository_root(self, project_path: Path) -> Path:
        result = self._run(["git", "rev-parse", "--show-toplevel"], project_path)
        if result.returncode != 0:
            raise RecommendationVerificationError("Candidate project is not inside a Git repository.")
        return Path(result.stdout.strip())

    def _branch_exists(self, repository: Path, branch_name: str) -> bool:
        result = self._run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"], repository)
        return result.returncode == 0

    def _branch_name(self, project_id: str, recommendations: RecommendationResult) -> str:
        fingerprint = hashlib.sha256(recommendations.model_dump_json().encode("utf-8")).hexdigest()[:10]
        safe_project_id = re.sub(r"[^A-Za-z0-9._-]+", "-", project_id).strip("-") or "project"
        return f"agent5/verification/{safe_project_id}-{fingerprint}"

    def _apply_requirement_replacement(self, path: Path, package_name: str, suggested_package: str | None) -> None:
        if suggested_package is None or not path.is_file():
            raise RecommendationVerificationError(f"Cannot apply replacement for {package_name}.")
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        pattern = re.compile(r"^(?P<indent>\s*)(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]+\])?(?:\s*(?:===|==|!=|<=|>=|~=|<|>).*)?$")
        replacement_count = 0
        updated = []
        for line in lines:
            declaration, separator, comment = line.partition("#")
            match = pattern.fullmatch(declaration.rstrip("\r\n"))
            if match and match.group("name").casefold() == package_name.casefold():
                newline = "\r\n" if declaration.endswith("\r\n") else "\n" if declaration.endswith("\n") else ""
                updated.append(f"{match.group('indent')}{suggested_package}{separator}{comment.rstrip(chr(10)).rstrip(chr(13))}{newline}" if separator else f"{match.group('indent')}{suggested_package}{newline}")
                replacement_count += 1
            else:
                updated.append(line)
        if replacement_count != 1:
            raise RecommendationVerificationError(f"Expected exactly one declaration for {package_name}; found {replacement_count}.")
        path.write_text("".join(updated), encoding="utf-8")

    def _modified_files(self, worktree: Path) -> set[str]:
        result = self._run(["git", "status", "--porcelain"], worktree)
        if result.returncode != 0:
            raise RecommendationVerificationError("Unable to inspect candidate modifications.")
        return {line[3:].replace("\\", "/") for line in result.stdout.splitlines() if len(line) > 3}

    def _run_project_tests(self, worktree: Path, python: Path) -> tuple[bool, bool | None]:
        test_files = list(worktree.rglob("test_*.py")) + list(worktree.rglob("*_test.py"))
        if not test_files and not (worktree / "tests").is_dir():
            return False, None
        result = self._run([str(python), "-m", "pytest", "-q"], worktree)
        return True, result.returncode == 0

    def _require(self, command: list[str], cwd: Path) -> None:
        result = self._run(command, cwd)
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "command failed"
            raise RecommendationVerificationError(f"{' '.join(command[:3])}: {detail}")

    @staticmethod
    def _result(project_id: str, branch_name: str | None, status: VerificationStatus, tests_available: bool, tests_passed: bool | None, candidate_valid: bool, merge_allowed: bool, details: list[str]) -> VerificationResult:
        return VerificationResult(project_id=project_id, branch_name=branch_name, status=status, tests_available=tests_available, tests_passed=tests_passed, candidate_valid=candidate_valid, merge_allowed=merge_allowed, details=details)


def verify_recommendations(
    agent3_result: Mapping[str, Any],
    recommendation_result: RecommendationResult | Mapping[str, Any],
    project_directory: str | Path,
) -> VerificationResult:
    """Verify Agent 4 output and gate merging; never merges the candidate branch."""
    return RecommendationVerifier().verify(agent3_result, recommendation_result, project_directory)
