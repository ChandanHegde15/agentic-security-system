# Research Evaluation Dataset: Agentic Security System

This package contains the 65-case research evaluation dataset for the Agentic Security System.

## Reproducible generation

The dataset package is intentionally separate from the implementation repository. Set the implementation repository explicitly:

```bash
export AGENTIC_SECURITY_REPO=/path/to/agentic-security-system
cd dataset_package
python3 scripts/generate_dataset.py
```

The generator imports the local `scripts/cases_data.py`, executes Agents 1–5 against deterministic registry stubs, and writes the generated dataset to `<repo>/dataset/research_evaluation_dataset.json`.

## Validation

```bash
export AGENTIC_SECURITY_REPO=/path/to/agentic-security-system
export DATASET_PATH=/path/to/research_evaluation_dataset.json
python3 scripts/validate_dataset.py
```

The validator checks schema/consistency invariants, Agent 3 deterministic reproduction, Agent 4 evidence safety, Agent 5 gating, candidate-remediation invariants, and the recorded rejection stage for negative cases.

## Provenance

- Registry outcomes are deterministic stubs defined in `scripts/cases_data.py`.
- Candidate-remediation cases marked with a non-`normal` `remediation_runner` use fault-injected command runners; they are behavioral/gating tests, not empirical package-install/test results.
- Negative cases record whether the raw Agent 4 artifact is rejected by Agent 4 or by Agent 5.
