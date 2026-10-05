"""Definitions of all 65 evaluation cases for the Agentic Security System dataset."""

from agents.registry_verification.registries.pypi_client import RegistryClientError

CASES_DEFINITIONS = [
    # -------------------------------------------------------------------------
    # CATEGORY 1: End-to-End Pipeline & Benign/Risk Scenarios (Cases 1-32)
    # -------------------------------------------------------------------------
    {
        "case_id": "CASE-001",
        "project_id": "P001",
        "category": "dependency_extraction",
        "subcategory": "multi_dependency_verified",
        "description": "Standard multi-dependency Python project with 4 verified PyPI packages.",
        "files": {
            "requirements.txt": "pandas\nnumpy\nrequests\nflask\n",
            "app.py": "import pandas as pd\nimport numpy as np\nimport requests\nfrom flask import Flask\napp = Flask(__name__)\n",
        },
        "registry_pypi": {
            "pandas": {"name": "pandas", "version": "2.2.0"},
            "numpy": {"name": "numpy", "version": "1.26.4"},
            "requests": {"name": "requests", "version": "2.31.0"},
            "flask": {"name": "flask", "version": "3.0.2"},
        },
        "agent4_recommendations": [
            {"package_name": "pandas", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Standard verified dependency.", "evidence_referenced": [], "conditional": False},
            {"package_name": "numpy", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Standard verified dependency.", "evidence_referenced": [], "conditional": False},
            {"package_name": "requests", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Standard verified dependency.", "evidence_referenced": [], "conditional": False},
            {"package_name": "flask", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Standard verified dependency.", "evidence_referenced": [], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-002",
        "project_id": "P002",
        "category": "dependency_extraction",
        "subcategory": "version_constraints",
        "description": "Multi-dependency Python project declaring various version constraints.",
        "files": {
            "requirements.txt": "pandas>=2.0\nnumpy==2.0.0\nrequests>=2.30\nflask\n",
            "app.py": "# P002 sample app\n",
        },
        "registry_pypi": {
            "pandas": {"name": "pandas", "version": "2.2.0"},
            "numpy": {"name": "numpy", "version": "2.0.0"},
            "requests": {"name": "requests", "version": "2.31.0"},
            "flask": {"name": "flask", "version": "3.0.2"},
        },
        "agent4_recommendations": [
            {"package_name": "pandas", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Standard verified dependency.", "evidence_referenced": [], "conditional": False},
            {"package_name": "numpy", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Standard verified dependency.", "evidence_referenced": [], "conditional": False},
            {"package_name": "requests", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Standard verified dependency.", "evidence_referenced": [], "conditional": False},
            {"package_name": "flask", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Standard verified dependency.", "evidence_referenced": [], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-003",
        "project_id": "P003",
        "category": "risk_analysis",
        "subcategory": "not_found_without_similarity",
        "description": "Python project with verified packages and one not_found package without name similarity.",
        "files": {
            "requirements.txt": "pandas\nnumpy\nsuperfast-ai-99999\n",
        },
        "registry_pypi": {
            "pandas": {"name": "pandas", "version": "2.2.0"},
            "numpy": {"name": "numpy", "version": "1.26.4"},
            "superfast-ai-99999": None,
        },
        "agent4_recommendations": [
            {"package_name": "pandas", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "numpy", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "superfast-ai-99999", "action": "monitor", "suggested_package": None, "suggested_version": None, "confidence": 0.85, "reasoning": "Unregistered package.", "evidence_referenced": ["not_found"], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-004",
        "project_id": "P004",
        "category": "risk_analysis",
        "subcategory": "not_found_below_similarity_threshold",
        "description": "Python project with 'reqeusts' which has similarity 0.75 (< 0.80) to 'requests' in standard Levenshtein.",
        "files": {
            "requirements.txt": "pandas\nreqeusts\n",
        },
        "registry_pypi": {
            "pandas": {"name": "pandas", "version": "2.2.0"},
            "reqeusts": None,
        },
        "agent4_recommendations": [
            {"package_name": "pandas", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "reqeusts", "action": "investigate", "suggested_package": None, "suggested_version": None, "confidence": 0.85, "reasoning": "Not found in registry.", "evidence_referenced": ["not_found"], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-005",
        "project_id": "P005",
        "category": "dependency_extraction",
        "subcategory": "node_runtime_dependencies",
        "description": "Node project with runtime dependencies in package.json.",
        "files": {
            "package.json": '{"name":"p005","dependencies":{"express":"^5.0.0","axios":"^1.8.0"}}',
        },
        "registry_npm": {
            "express": {"name": "express", "version": "5.0.0"},
            "axios": {"name": "axios", "version": "1.8.0"},
        },
        "agent4_recommendations": [
            {"package_name": "express", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "axios", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-006",
        "project_id": "P006",
        "category": "risk_analysis",
        "subcategory": "node_not_found_without_similarity",
        "description": "Node project with one verified and one nonexistent package without similarity.",
        "files": {
            "package.json": '{"name":"p006","dependencies":{"express":"^5.0.0","super-ai-package-99999":"^1.0.0"}}',
        },
        "registry_npm": {
            "express": {"name": "express", "version": "5.0.0"},
            "super-ai-package-99999": None,
        },
        "agent4_recommendations": [
            {"package_name": "express", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "super-ai-package-99999", "action": "monitor", "suggested_package": None, "suggested_version": None, "confidence": 0.85, "reasoning": "Unregistered.", "evidence_referenced": ["not_found"], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-007",
        "project_id": "P007",
        "category": "risk_analysis",
        "subcategory": "node_moderate_similarity",
        "description": "Node project with 'expres' having moderate similarity (6/7=0.857) to reference package 'express'.",
        "files": {
            "package.json": '{"name":"p007","dependencies":{"express":"^5.0.0","expres":"^5.0.0"}}',
        },
        "registry_npm": {
            "express": {"name": "express", "version": "5.0.0"},
            "expres": None,
        },
        "agent4_recommendations": [
            {"package_name": "express", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "expres", "action": "replace", "suggested_package": "express", "suggested_version": None, "confidence": 0.90, "reasoning": "Moderate similarity.", "evidence_referenced": ["not_found", "name_similarity"], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-008",
        "project_id": "P008",
        "category": "dependency_extraction",
        "subcategory": "mixed_ecosystem",
        "description": "Mixed project containing both requirements.txt (pypi) and package.json (npm).",
        "files": {
            "requirements.txt": "pandas\nnumpy\nrequests\n",
            "package.json": '{"name":"p008","dependencies":{"express":"^5.0.0","axios":"^1.8.0"}}',
        },
        "registry_pypi": {
            "pandas": {"name": "pandas", "version": "2.2.0"},
            "numpy": {"name": "numpy", "version": "1.26.4"},
            "requests": {"name": "requests", "version": "2.31.0"},
        },
        "registry_npm": {
            "express": {"name": "express", "version": "5.0.0"},
            "axios": {"name": "axios", "version": "1.8.0"},
        },
        "agent4_recommendations": [
            {"package_name": "pandas", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "numpy", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "requests", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "express", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "axios", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-009",
        "category": "registry_verification",
        "subcategory": "single_verified_package",
        "description": "Single verified PyPI package with minimum version constraint.",
        "files": {
            "requirements.txt": "requests>=2.31.0\n",
        },
        "registry_pypi": {
            "requests": {"name": "requests", "version": "2.31.0"},
        },
        "agent4_action": "no_action",
    },
    {
        "case_id": "CASE-010",
        "category": "risk_analysis",
        "subcategory": "pypi_moderate_similarity",
        "description": "'request' not found on PyPI with moderate similarity (7/8=0.875) to 'requests'.",
        "files": {
            "requirements.txt": "request\n",
        },
        "registry_pypi": {
            "request": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "requests",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
    },
    {
        "case_id": "CASE-011",
        "category": "risk_analysis",
        "subcategory": "pypi_moderate_similarity",
        "description": "'pandass' not found on PyPI with moderate similarity (6/7=0.857) to 'pandas'.",
        "files": {
            "requirements.txt": "pandass\n",
        },
        "registry_pypi": {
            "pandass": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "pandas",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
    },
    {
        "case_id": "CASE-012",
        "category": "risk_analysis",
        "subcategory": "pypi_moderate_similarity",
        "description": "'numpi' not found on PyPI with moderate similarity (4/5=0.80) to 'numpy'.",
        "files": {
            "requirements.txt": "numpi\n",
        },
        "registry_pypi": {
            "numpi": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "numpy",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
    },
    {
        "case_id": "CASE-013",
        "category": "risk_analysis",
        "subcategory": "pypi_moderate_similarity",
        "description": "'flasks' not found on PyPI with moderate similarity (5/6=0.833) to 'flask'.",
        "files": {
            "requirements.txt": "flasks\n",
        },
        "registry_pypi": {
            "flasks": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "flask",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
    },
    {
        "case_id": "CASE-014",
        "category": "risk_analysis",
        "subcategory": "npm_moderate_similarity",
        "description": "'axio' not found on npm with moderate similarity (4/5=0.80) to 'axios'.",
        "files": {
            "package.json": '{"dependencies":{"axio":"^1.0.0"}}',
        },
        "registry_npm": {
            "axio": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "axios",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
    },
    {
        "case_id": "CASE-015",
        "category": "risk_analysis",
        "subcategory": "npm_moderate_similarity",
        "description": "'reactt' not found on npm with moderate similarity (5/6=0.833) to 'react'.",
        "files": {
            "package.json": '{"dependencies":{"reactt":"^18.0.0"}}',
        },
        "registry_npm": {
            "reactt": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "react",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
    },
    {
        "case_id": "CASE-016",
        "category": "risk_analysis",
        "subcategory": "strong_similarity_exact_name_not_found",
        "description": "Package named 'requests' not found in registry; exact name match yields similarity 1.0 (strong similarity >= 0.90).",
        "files": {
            "requirements.txt": "requests\n",
        },
        "registry_pypi": {
            "requests": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "requests",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
    },
    {
        "case_id": "CASE-017",
        "category": "risk_analysis",
        "subcategory": "strong_similarity_custom_catalogue",
        "description": "'tensorflw' with custom catalogue containing 'tensorflow'; distance 1, similarity 9/10=0.90 (strong similarity >= 0.90).",
        "files": {
            "requirements.txt": "tensorflw\n",
        },
        "registry_pypi": {
            "tensorflw": None,
        },
        "custom_reference_packages": {
            "pypi": ("tensorflow",),
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "tensorflow",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
    },
    {
        "case_id": "CASE-018",
        "category": "risk_analysis",
        "subcategory": "strong_similarity_custom_catalogue",
        "description": "'beautifulsoup' with custom catalogue containing 'beautifulsoup4'; distance 1, similarity 13/14=0.9286 (strong similarity >= 0.90).",
        "files": {
            "requirements.txt": "beautifulsoup\n",
        },
        "registry_pypi": {
            "beautifulsoup": None,
        },
        "custom_reference_packages": {
            "pypi": ("beautifulsoup4",),
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "beautifulsoup4",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
    },
    {
        "case_id": "CASE-019",
        "category": "risk_analysis",
        "subcategory": "moderate_similarity_custom_catalogue",
        "description": "'typescrip' with custom npm catalogue containing 'typescript'; distance 1, similarity 9/10=0.90 (strong similarity >= 0.90).",
        "files": {
            "package.json": '{"dependencies":{"typescrip":"^5.0.0"}}',
        },
        "registry_npm": {
            "typescrip": None,
        },
        "custom_reference_packages": {
            "npm": ("typescript",),
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "typescript",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
    },
    {
        "case_id": "CASE-020",
        "category": "registry_verification",
        "subcategory": "pypi_registry_error",
        "description": "PyPI registry connection timeout causing registry_error status and unknown risk.",
        "files": {
            "requirements.txt": "requests\n",
        },
        "registry_pypi": {
            "requests": RegistryClientError("PyPI request timed out"),
        },
        "agent4_action": "review",
        "agent4_conditional": True,
        "agent4_evidence_referenced": ["registry_error"],
    },
    {
        "case_id": "CASE-021",
        "category": "registry_verification",
        "subcategory": "npm_registry_error",
        "description": "npm registry HTTP 503 response causing registry_error status and unknown risk.",
        "files": {
            "package.json": '{"dependencies":{"express":"^5.0.0"}}',
        },
        "registry_npm": {
            "express": RegistryClientError("npm returned HTTP 503"),
        },
        "agent4_action": "insufficient_evidence",
        "agent4_conditional": True,
        "agent4_evidence_referenced": ["registry_error"],
    },
    {
        "case_id": "CASE-022",
        "category": "registry_verification",
        "subcategory": "unsupported_ecosystem_handling",
        "description": "Dependency declaration in requirements.txt with registry returning unsupported ecosystem outcome.",
        "files": {
            "requirements.txt": "unsupported-sys-pkg\n",
        },
        "registry_pypi": {
            "unsupported-sys-pkg": None,
        },
        # We simulate unsupported ecosystem by custom client or let verify_dependencies map
        "agent4_action": "review",
        "agent4_conditional": True,
        "agent4_evidence_referenced": ["not_found"],
    },
    {
        "case_id": "CASE-023",
        "category": "risk_analysis",
        "subcategory": "not_found_action_investigate",
        "description": "Unregistered package 'random-internal-lib-xyz' evaluated with investigate action.",
        "files": {
            "requirements.txt": "random-internal-lib-xyz\n",
        },
        "registry_pypi": {
            "random-internal-lib-xyz": None,
        },
        "agent4_action": "investigate",
        "agent4_evidence_referenced": ["not_found"],
    },
    {
        "case_id": "CASE-024",
        "category": "dependency_extraction",
        "subcategory": "compound_version_constraints",
        "description": "Python package declaring compound version bounds: 'urllib3>=1.26.0,<3.0.0'.",
        "files": {
            "requirements.txt": "urllib3>=1.26.0,<3.0.0\n",
        },
        "registry_pypi": {
            "urllib3": {"name": "urllib3", "version": "2.2.1"},
        },
        "agent4_action": "no_action",
    },
    {
        "case_id": "CASE-025",
        "category": "pipeline_integration",
        "subcategory": "mixed_status_project",
        "description": "Project with 1 verified, 1 not_found with moderate similarity, and 1 not_found without similarity.",
        "files": {
            "requirements.txt": "flask\nrequest\nrandom-ai-lib-123\n",
        },
        "registry_pypi": {
            "flask": {"name": "flask", "version": "3.0.2"},
            "request": None,
            "random-ai-lib-123": None,
        },
        "agent4_recommendations": [
            {"package_name": "flask", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "request", "action": "replace", "suggested_package": "requests", "suggested_version": None, "confidence": 0.90, "reasoning": "Moderate similarity.", "evidence_referenced": ["not_found", "name_similarity"], "conditional": False},
            {"package_name": "random-ai-lib-123", "action": "monitor", "suggested_package": None, "suggested_version": None, "confidence": 0.85, "reasoning": "Unregistered.", "evidence_referenced": ["not_found"], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-026",
        "category": "pipeline_integration",
        "subcategory": "mixed_verified_and_registry_error",
        "description": "Project with 1 verified package and 1 package encountering registry timeout.",
        "files": {
            "requirements.txt": "numpy\npandas\n",
        },
        "registry_pypi": {
            "numpy": {"name": "numpy", "version": "1.26.4"},
            "pandas": RegistryClientError("PyPI timeout"),
        },
        "agent4_recommendations": [
            {"package_name": "numpy", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "pandas", "action": "review", "suggested_package": None, "suggested_version": None, "confidence": 0.80, "reasoning": "Recommended action: review. Evidence: Registry verification was unavailable; risk cannot be calculated.", "evidence_referenced": ["registry_error"], "conditional": True},
        ],
    },
    {
        "case_id": "CASE-027",
        "category": "pipeline_integration",
        "subcategory": "mixed_npm_project",
        "description": "npm project with 1 verified, 1 moderate similarity candidate, and 1 unregistered utility.",
        "files": {
            "package.json": '{"dependencies":{"react":"^18.2.0","expres":"^5.0.0","custom-analytics-pkg":"^1.0.0"}}',
        },
        "registry_npm": {
            "react": {"name": "react", "version": "18.2.0"},
            "expres": None,
            "custom-analytics-pkg": None,
        },
        "agent4_recommendations": [
            {"package_name": "react", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "expres", "action": "replace", "suggested_package": "express", "suggested_version": None, "confidence": 0.90, "reasoning": "Moderate similarity.", "evidence_referenced": ["not_found", "name_similarity"], "conditional": False},
            {"package_name": "custom-analytics-pkg", "action": "monitor", "suggested_package": None, "suggested_version": None, "confidence": 0.85, "reasoning": "Unregistered.", "evidence_referenced": ["not_found"], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-028",
        "category": "dependency_extraction",
        "subcategory": "empty_manifest",
        "description": "Empty requirements.txt containing only comments and blank lines.",
        "files": {
            "requirements.txt": "# Only comments\n\n   # Indented comment\n",
        },
        "agent4_recommendations": [],
    },
    {
        "case_id": "CASE-029",
        "category": "dependency_extraction",
        "subcategory": "duplicate_declarations",
        "description": "Requirements file containing duplicate declarations deduplicated by Agent 1.",
        "files": {
            "requirements.txt": "pandas\npandas\nnumpy==2.0\nnumpy==2.0\n",
        },
        "registry_pypi": {
            "pandas": {"name": "pandas", "version": "2.2.0"},
            "numpy": {"name": "numpy", "version": "2.0.0"},
        },
        "agent4_recommendations": [
            {"package_name": "pandas", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "numpy", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-030",
        "category": "dependency_extraction",
        "subcategory": "tilde_version_constraint",
        "description": "Python package declaring compatible release constraint 'flask~=3.0'.",
        "files": {
            "requirements.txt": "flask~=3.0\n",
        },
        "registry_pypi": {
            "flask": {"name": "flask", "version": "3.0.2"},
        },
        "agent4_action": "no_action",
    },
    {
        "case_id": "CASE-031",
        "category": "dependency_extraction",
        "subcategory": "npm_version_syntax",
        "description": "npm dependencies declaring caret and tilde ranges.",
        "files": {
            "package.json": '{"dependencies":{"express":"^5.0.0","axios":"~1.2.3"}}',
        },
        "registry_npm": {
            "express": {"name": "express", "version": "5.0.0"},
            "axios": {"name": "axios", "version": "1.2.3"},
        },
        "agent4_recommendations": [
            {"package_name": "express", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
            {"package_name": "axios", "action": "no_action", "suggested_package": None, "suggested_version": None, "confidence": 0.95, "reasoning": "Verified.", "evidence_referenced": [], "conditional": False},
        ],
    },
    {
        "case_id": "CASE-032",
        "category": "risk_analysis",
        "subcategory": "not_found_action_monitor",
        "description": "Nonexistent package 'unregistered-internal-toolkit' assigned monitor action.",
        "files": {
            "requirements.txt": "unregistered-internal-toolkit\n",
        },
        "registry_pypi": {
            "unregistered-internal-toolkit": None,
        },
        "agent4_action": "monitor",
        "agent4_evidence_referenced": ["not_found"],
    },

    # -------------------------------------------------------------------------
    # CATEGORY 2: Candidate Remediation & Merge Gate Scenarios (Cases 33-42)
    # -------------------------------------------------------------------------
    {
        "case_id": "CASE-033",
        "category": "candidate_remediation",
        "subcategory": "remediation_success",
        "description": "Python replacement candidate applied in isolated worktree, project tests pass, merge authorized.",
        "files": {
            "requirements.txt": "request\n",
            "test_candidate.py": "def test_ok():\n    assert True\n",
        },
        "registry_pypi": {
            "request": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "requests",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
        "remediation_runner": "normal",
    },
    {
        "case_id": "CASE-034",
        "category": "candidate_remediation",
        "subcategory": "remediation_test_failure",
        "description": "Python replacement candidate applied, but project test suite fails; merge blocked.",
        "files": {
            "requirements.txt": "flasks\n",
            "test_candidate.py": "def test_candidate():\n    assert True\n",
        },
        "registry_pypi": {
            "flasks": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "flask",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
        "remediation_runner": "test_failure",
    },
    {
        "case_id": "CASE-035",
        "category": "candidate_remediation",
        "subcategory": "remediation_no_tests",
        "description": "Python replacement candidate applied, but project contains no test suite; merge not authorized.",
        "files": {
            "requirements.txt": "pandass\n",
            "main.py": "# No test files\n",
        },
        "registry_pypi": {
            "pandass": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "pandas",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
        "remediation_runner": "normal",
    },
    {
        "case_id": "CASE-036",
        "category": "candidate_remediation",
        "subcategory": "remediation_install_failure",
        "description": "Python replacement candidate fails pip installation in isolated venv; merge blocked.",
        "files": {
            "requirements.txt": "numpi\n",
            "test_candidate.py": "def test_candidate():\n    assert True\n",
        },
        "registry_pypi": {
            "numpi": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "numpy",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
        "remediation_runner": "install_failure",
    },
    {
        "case_id": "CASE-037",
        "category": "candidate_remediation",
        "subcategory": "remediation_unsupported_ecosystem",
        "description": "npm replacement candidate fails closed because Agent 5 only supports requirements.txt candidate remediation.",
        "files": {
            "package.json": '{"dependencies":{"expres":"^5.0.0"}}',
        },
        "registry_npm": {
            "expres": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "express",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
        "remediation_runner": "normal",
    },
    {
        "case_id": "CASE-038",
        "category": "candidate_remediation",
        "subcategory": "remediation_non_replacement_no_action",
        "description": "Recommendation action is no_action; Agent 5 returns requires_review as no candidate replacement exists.",
        "files": {
            "requirements.txt": "requests\n",
            "test_candidate.py": "def test_candidate():\n    assert True\n",
        },
        "registry_pypi": {
            "requests": {"name": "requests", "version": "2.31.0"},
        },
        "agent4_action": "no_action",
        "remediation_runner": "normal",
    },
    {
        "case_id": "CASE-039",
        "category": "candidate_remediation",
        "subcategory": "remediation_non_replacement_monitor",
        "description": "Recommendation action is monitor; Agent 5 returns requires_review as no candidate replacement exists.",
        "files": {
            "requirements.txt": "superfast-ai-99999\n",
            "test_candidate.py": "def test_candidate():\n    assert True\n",
        },
        "registry_pypi": {
            "superfast-ai-99999": None,
        },
        "agent4_action": "monitor",
        "agent4_evidence_referenced": ["not_found"],
        "remediation_runner": "normal",
    },
    {
        "case_id": "CASE-040",
        "category": "candidate_remediation",
        "subcategory": "remediation_non_replacement_investigate",
        "description": "Recommendation action is investigate; Agent 5 returns requires_review without merge authorization.",
        "files": {
            "requirements.txt": "reqeusts\n",
            "test_candidate.py": "def test_candidate():\n    assert True\n",
        },
        "registry_pypi": {
            "reqeusts": None,
        },
        "agent4_action": "investigate",
        "agent4_evidence_referenced": ["not_found"],
        "remediation_runner": "normal",
    },
    {
        "case_id": "CASE-041",
        "category": "candidate_remediation",
        "subcategory": "remediation_branch_collision",
        "description": "Verification branch already exists in repository; Agent 5 refuses to overwrite and blocks merge.",
        "files": {
            "requirements.txt": "request\n",
            "test_candidate.py": "def test_candidate():\n    assert True\n",
        },
        "registry_pypi": {
            "request": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "requests",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
        "remediation_runner": "branch_collision",
    },
    {
        "case_id": "CASE-042",
        "category": "candidate_remediation",
        "subcategory": "remediation_unexpected_modifications",
        "description": "Worktree modification introduces changes outside requirements.txt; rejected fail-closed.",
        "files": {
            "requirements.txt": "request\n",
            "test_candidate.py": "def test_candidate():\n    assert True\n",
        },
        "registry_pypi": {
            "request": None,
        },
        "agent4_action": "replace",
        "agent4_suggested_package": "requests",
        "agent4_evidence_referenced": ["not_found", "name_similarity"],
        "remediation_runner": "unexpected_modifications",
    },

    # -------------------------------------------------------------------------
    # CATEGORY 3: Negative Agent 4 Artifact Under Test Scenarios (Cases 43-65)
    # -------------------------------------------------------------------------
    {
        "case_id": "CASE-043",
        "category": "negative_agent_4",
        "subcategory": "unsupported_evidence_cve",
        "description": "Agent 4 references 'cve' evidence not supplied by Agent 3.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Recommendation for request cites unsupported evidence: ['cve']",
        "agent4_artifact_under_test": {
            "project_id": "CASE-043",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "investigate",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Investigate based on CVE.",
                    "evidence_referenced": ["not_found", "cve"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-044",
        "category": "negative_agent_4",
        "subcategory": "unsupported_evidence_malware",
        "description": "Agent 4 references 'malware' evidence not supplied by Agent 3.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Recommendation for request cites unsupported evidence: ['malware']",
        "agent4_artifact_under_test": {
            "project_id": "CASE-044",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "investigate",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Investigate malware.",
                    "evidence_referenced": ["not_found", "malware"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-045",
        "category": "negative_agent_4",
        "subcategory": "fake_replacement_package",
        "description": "Agent 4 suggests 'safe-requests' which was not supplied as reference package by Agent 3.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Replacement package is not backed by Agent 3 evidence",
        "agent4_artifact_under_test": {
            "project_id": "CASE-045",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "replace",
                    "suggested_package": "safe-requests",
                    "suggested_version": None,
                    "confidence": 0.9,
                    "reasoning": "Replace with safe-requests.",
                    "evidence_referenced": ["not_found", "name_similarity"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-046",
        "category": "negative_agent_4",
        "subcategory": "unsupported_replacement_package",
        "description": "Agent 4 suggests 'urllib3' when Agent 3 reference package was 'requests'.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Replacement package is not backed by Agent 3 evidence",
        "agent4_artifact_under_test": {
            "project_id": "CASE-046",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "replace",
                    "suggested_package": "urllib3",
                    "suggested_version": None,
                    "confidence": 0.9,
                    "reasoning": "Replace with urllib3.",
                    "evidence_referenced": ["not_found", "name_similarity"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-047",
        "category": "negative_agent_4",
        "subcategory": "replace_without_suggested_package",
        "description": "Agent 4 proposes replace action but leaves suggested_package as null.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Replacement action for request requires suggested_package",
        "agent4_artifact_under_test": {
            "project_id": "CASE-047",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "replace",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.9,
                    "reasoning": "Replace action missing package.",
                    "evidence_referenced": ["not_found", "name_similarity"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-048",
        "category": "negative_agent_5",
        "subcategory": "replace_without_name_similarity",
        "description": "Agent 4 proposes replace action without referencing name_similarity evidence.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Replacement requires referenced name_similarity evidence",
        "agent4_artifact_under_test": {
            "project_id": "CASE-048",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "replace",
                    "suggested_package": "requests",
                    "suggested_version": None,
                    "confidence": 0.9,
                    "reasoning": "Replace without citing name similarity.",
                    "evidence_referenced": ["not_found"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-049",
        "category": "negative_agent_5",
        "subcategory": "suggested_package_on_investigate",
        "description": "Agent 4 suggests a package on an investigate action.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Only replacement recommendations may suggest a package",
        "agent4_artifact_under_test": {
            "project_id": "CASE-049",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "investigate",
                    "suggested_package": "requests",
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Investigate with suggested package.",
                    "evidence_referenced": ["not_found"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-050",
        "category": "negative_agent_5",
        "subcategory": "suggested_package_on_no_action",
        "description": "Agent 4 suggests a package on a no_action recommendation.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "requests\n"},
        "registry_pypi": {"requests": {"name": "requests", "version": "2.31.0"}},
        "expected_error": "Only replacement recommendations may suggest a package",
        "agent4_artifact_under_test": {
            "project_id": "CASE-050",
            "recommendations": [
                {
                    "package_name": "requests",
                    "action": "no_action",
                    "suggested_package": "requests",
                    "suggested_version": None,
                    "confidence": 0.95,
                    "reasoning": "No action with package attached.",
                    "evidence_referenced": [],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-051",
        "category": "negative_agent_4",
        "subcategory": "invented_version_on_replace",
        "description": "Agent 4 invents replacement version '2.32.3' not provided as authoritative evidence.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Suggested versions are not authoritative in the current Agent 3 contract",
        "agent4_artifact_under_test": {
            "project_id": "CASE-051",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "replace",
                    "suggested_package": "requests",
                    "suggested_version": "2.32.3",
                    "confidence": 0.9,
                    "reasoning": "Replace with invented version.",
                    "evidence_referenced": ["not_found", "name_similarity"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-052",
        "category": "negative_agent_4",
        "subcategory": "invented_version_on_no_action",
        "description": "Agent 4 provides suggested_version '1.0.0' on no_action recommendation.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "requests\n"},
        "registry_pypi": {"requests": {"name": "requests", "version": "2.31.0"}},
        "expected_error": "Suggested versions are not authoritative in the current Agent 3 contract",
        "agent4_artifact_under_test": {
            "project_id": "CASE-052",
            "recommendations": [
                {
                    "package_name": "requests",
                    "action": "no_action",
                    "suggested_package": None,
                    "suggested_version": "1.0.0",
                    "confidence": 0.95,
                    "reasoning": "No action with version.",
                    "evidence_referenced": [],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-053",
        "category": "negative_agent_5",
        "subcategory": "unknown_risk_not_conditional",
        "description": "Dependency has registry_error (unknown risk) but Agent 4 sets conditional=False.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "requests\n"},
        "registry_pypi": {"requests": RegistryClientError("timeout")},
        "expected_error": "Unknown Agent 3 states require a conditional review or insufficient_evidence recommendation",
        "agent4_artifact_under_test": {
            "project_id": "CASE-053",
            "recommendations": [
                {
                    "package_name": "requests",
                    "action": "review",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Review without conditional.",
                    "evidence_referenced": ["registry_error"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-054",
        "category": "negative_agent_4",
        "subcategory": "unknown_risk_disallowed_action_replace",
        "description": "Dependency has unknown risk (registry_error) but Agent 4 recommends replace.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "requests\n"},
        "registry_pypi": {"requests": RegistryClientError("timeout")},
        "expected_error": "Unknown Agent 3 states require a conditional review or insufficient_evidence recommendation",
        "agent4_artifact_under_test": {
            "project_id": "CASE-054",
            "recommendations": [
                {
                    "package_name": "requests",
                    "action": "replace",
                    "suggested_package": "requests",
                    "suggested_version": None,
                    "confidence": 0.9,
                    "reasoning": "Replace on unknown risk.",
                    "evidence_referenced": ["registry_error"],
                    "conditional": True,
                }
            ],
        },
    },
    {
        "case_id": "CASE-055",
        "category": "negative_agent_5",
        "subcategory": "unknown_risk_disallowed_action_no_action",
        "description": "Dependency has unknown risk (registry_error) but Agent 4 recommends no_action.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "requests\n"},
        "registry_pypi": {"requests": RegistryClientError("timeout")},
        "expected_error": "Unknown Agent 3 states require a conditional review or insufficient_evidence recommendation",
        "agent4_artifact_under_test": {
            "project_id": "CASE-055",
            "recommendations": [
                {
                    "package_name": "requests",
                    "action": "no_action",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.95,
                    "reasoning": "No action on unknown risk.",
                    "evidence_referenced": ["registry_error"],
                    "conditional": True,
                }
            ],
        },
    },
    {
        "case_id": "CASE-056",
        "category": "negative_agent_5",
        "subcategory": "ungrounded_reasoning_malware",
        "description": "Agent 4 reasoning asserts ungrounded claim that the package is 'malware'.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Recommendation reasoning for request is not grounded in Agent 3 evidence",
        "agent4_artifact_under_test": {
            "project_id": "CASE-056",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "investigate",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Recommended action: investigate. This package is malware.",
                    "evidence_referenced": ["not_found"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-057",
        "category": "negative_agent_5",
        "subcategory": "ungrounded_reasoning_typosquatting",
        "description": "Agent 4 reasoning asserts ungrounded claim of 'intentional typo-squatting'.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Recommendation reasoning for request is not grounded in Agent 3 evidence",
        "agent4_artifact_under_test": {
            "project_id": "CASE-057",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "investigate",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Recommended action: investigate. This is intentional typo-squatting.",
                    "evidence_referenced": ["not_found"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-058",
        "category": "negative_agent_5",
        "subcategory": "ungrounded_reasoning_compromised",
        "description": "Agent 4 reasoning asserts ungrounded claim that the package is 'compromised'.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Recommendation reasoning for request is not grounded in Agent 3 evidence",
        "agent4_artifact_under_test": {
            "project_id": "CASE-058",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "investigate",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Recommended action: investigate. This package is compromised.",
                    "evidence_referenced": ["not_found"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-059",
        "category": "negative_agent_5",
        "subcategory": "contradictory_reasoning_exists",
        "description": "Agent 4 reasoning asserts that package exists in official registry when status is not_found.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Recommendation reasoning for request is not grounded in Agent 3 evidence",
        "agent4_artifact_under_test": {
            "project_id": "CASE-059",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "investigate",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Recommended action: investigate. The package exists in the official registry.",
                    "evidence_referenced": ["not_found"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-060",
        "category": "negative_agent_4",
        "subcategory": "project_id_mismatch",
        "description": "Agent 4 recommendation output belongs to a different project ID.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Agent 3 and Agent 4 project IDs do not match",
        "agent4_artifact_under_test": {
            "project_id": "WRONG_PROJECT",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "investigate",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.8,
                    "reasoning": "Recommended action: investigate.",
                    "evidence_referenced": ["not_found"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-061",
        "category": "negative_agent_5",
        "subcategory": "coverage_mismatch_missing_dependency",
        "description": "Agent 4 omits recommendation for 'numpy' present in Agent 3 dependencies.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "requests\nnumpy\n"},
        "registry_pypi": {
            "requests": {"name": "requests", "version": "2.31.0"},
            "numpy": {"name": "numpy", "version": "1.26.4"},
        },
        "expected_error": "Recommendation coverage does not match Agent 3 dependencies; missing=['numpy'], unknown=[]",
        "agent4_artifact_under_test": {
            "project_id": "CASE-061",
            "recommendations": [
                {
                    "package_name": "requests",
                    "action": "no_action",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.95,
                    "reasoning": "Recommended action: no_action. No Agent 3 signals were referenced for this recommendation.",
                    "evidence_referenced": [],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-062",
        "category": "negative_agent_4",
        "subcategory": "coverage_mismatch_extraneous_package",
        "description": "Agent 4 provides an extraneous recommendation for 'phantom-pkg' not in Agent 3.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "requests\n"},
        "registry_pypi": {"requests": {"name": "requests", "version": "2.31.0"}},
        "expected_error": "Recommendation coverage does not match Agent 3 dependencies; missing=[], unknown=['phantom-pkg']",
        "agent4_artifact_under_test": {
            "project_id": "CASE-062",
            "recommendations": [
                {
                    "package_name": "requests",
                    "action": "no_action",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.95,
                    "reasoning": "Recommended action: no_action. No Agent 3 signals were referenced for this recommendation.",
                    "evidence_referenced": [],
                    "conditional": False,
                },
                {
                    "package_name": "phantom-pkg",
                    "action": "no_action",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.95,
                    "reasoning": "Recommended action: no_action. No Agent 3 signals were referenced for this recommendation.",
                    "evidence_referenced": [],
                    "conditional": False,
                },
            ],
        },
    },
    {
        "case_id": "CASE-063",
        "category": "negative_agent_5",
        "subcategory": "duplicate_recommendations",
        "description": "Agent 4 contains duplicate recommendations for the same package 'requests'.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent5",
        "files": {"requirements.txt": "requests\n"},
        "registry_pypi": {"requests": {"name": "requests", "version": "2.31.0"}},
        "expected_error": "Duplicate recommendations are not allowed",
        "agent4_artifact_under_test": {
            "project_id": "CASE-063",
            "recommendations": [
                {
                    "package_name": "requests",
                    "action": "no_action",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.95,
                    "reasoning": "First recommendation.",
                    "evidence_referenced": [],
                    "conditional": False,
                },
                {
                    "package_name": "requests",
                    "action": "no_action",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.95,
                    "reasoning": "Duplicate recommendation.",
                    "evidence_referenced": [],
                    "conditional": False,
                },
            ],
        },
    },
    {
        "case_id": "CASE-064",
        "category": "negative_agent_4",
        "subcategory": "disallowed_action_enum",
        "description": "Agent 4 uses disallowed action 'quarantine' not in RecommendationAction enum.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Input should be 'no_action', 'monitor', 'investigate', 'replace', 'review' or 'insufficient_evidence'",
        "agent4_artifact_under_test": {
            "project_id": "CASE-064",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "quarantine",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 0.9,
                    "reasoning": "Quarantine action.",
                    "evidence_referenced": ["not_found"],
                    "conditional": False,
                }
            ],
        },
    },
    {
        "case_id": "CASE-065",
        "category": "negative_agent_4",
        "subcategory": "invalid_confidence_score",
        "description": "Agent 4 specifies confidence 1.5 exceeding upper bound 1.0.",
        "is_negative_test": True,
        "expected_rejection_stage": "agent4",
        "files": {"requirements.txt": "request\n"},
        "registry_pypi": {"request": None},
        "expected_error": "Input should be less than or equal to 1",
        "agent4_artifact_under_test": {
            "project_id": "CASE-065",
            "recommendations": [
                {
                    "package_name": "request",
                    "action": "investigate",
                    "suggested_package": None,
                    "suggested_version": None,
                    "confidence": 1.5,
                    "reasoning": "Invalid confidence.",
                    "evidence_referenced": ["not_found"],
                    "conditional": False,
                }
            ],
        },
    },
]
