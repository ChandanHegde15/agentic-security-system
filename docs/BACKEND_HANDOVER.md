# Backend handover: Agentic Dependency Security System

## Status

This repository has a callable Python pipeline and passing unit/integration tests for the pipeline with a mock LLM provider. The fine-tuned local Qwen adapter was trained and saved, but **the local model has not yet passed end-to-end integration validation**. The frozen benchmark metrics do not demonstrate an improvement over the baseline.

Do not retrain as part of frontend integration. Do not modify Agent 3 risk scoring, Agent 5 verification rules, or the frozen 65-case benchmark to improve reported results.

## Pipeline entry point

```python
from agents.pipeline import run_pipeline
from agents.recommendation.llm.local_qwen_provider import LocalQwenProvider

provider = LocalQwenProvider(
    adapter_path="models/agent4_recovered_adapters/final_adapter",
    base_model="Qwen/Qwen2.5-0.5B-Instruct",
)
result = run_pipeline("test-projects/P001", llm_provider=provider)
```

`run_pipeline(project_directory, *, llm_provider, pypi_client=None, npm_client=None, recommendation_verifier=None)` runs dependency extraction, registry verification, deterministic risk analysis, Agent 4 recommendations, and Agent 5 recommendation verification. The registry clients, LLM provider, and Agent 5 verifier can be injected for offline tests.

The default registry clients are used when no clients are injected. A local model requires compatible `torch`, `transformers`, and `peft` installations and the base model in the local Hugging Face cache. `LocalQwenProvider` deliberately uses `local_files_only=True`; it will not download model files automatically.

## Output contract

The return value is a JSON-serializable dictionary with these top-level fields:

- `project_id`: identifier assigned by dependency extraction.
- `extraction`: extracted project dependencies and source-file information.
- `verification`: registry verification results.
- `risk_analysis`: Agent 3 scores, levels, signals, and evidence.
- `recommendations`: Agent 4's validated recommendation result (`project_id` and `recommendations`).
- `recommendation_verification`: Agent 5 verification result, including status and `merge_allowed`.
- `merge_allowed`: convenience copy of `recommendation_verification.merge_allowed`.

Each recommendation contains the package name, action, optional suggested package/version, confidence, reasoning, evidence references, and conditional flag. The authoritative field definitions and allowed values are in `agents/recommendation/models.py`; do not hard-code frontend assumptions that contradict those models.

## Frontend integration guidance

Keep the frontend separate from the Python agents. A backend/API layer should:

1. Accept an uploaded project archive or supported dependency files.
2. Store/extract them into an isolated temporary directory with archive traversal protections and size limits.
3. Call `run_pipeline` with the configured provider and registry clients.
4. Return the serialized result and a clear error status if extraction, model generation, or validation fails.
5. Never treat `merge_allowed` as proof that arbitrary code is safe; it reflects the existing Agent 5 validation flow only.

Do not return API keys, local filesystem paths, stack traces, or raw secret-bearing environment values to the browser. Do not silently replace a failed model call with mock output in production.

## Evaluation artifacts and limitations

The adapter's `training_metrics.json`, `internal_test_metrics.json`, `external_benchmark_metrics.json`, and baseline evaluation files are research artifacts. Keep the original frozen benchmark unchanged and never use it for training.

The external prediction artifact contains 65 rows, all with parsed predictions. Of these, 23 rows have a recorded `AttributeError` and null expected labels; 42 rows have non-null expected labels. The origin of the recorded errors cannot be established because the evaluator implementation is unavailable. These rows must not be treated as ordinary exact-match cases, nor can they be definitively attributed to the model or evaluator. Among the 42 scorable cases, 3 match the full expected object (7.14%). Package-action agreement is 39/64 comparisons (60.94%). Remaining mismatches are retained and reported without attributing them to evaluator defects.

The audit script, `scripts/audit_external_benchmark.py`, reads the saved records without rewriting them or treating null expected labels as ordinary exact-match cases. It cannot reconstruct the missing evaluator's full logic.

## Validation commands

Run these commands from the repository root in the intended project environment:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q --basetemp .pytest_tmp
python scripts/audit_external_benchmark.py
python scripts/test_agent4_local.py
```

The automated test suite most recently passed with **72 tests passed and 12 subtests passed**. This confirms the current automated tests pass; it does not establish successful end-to-end inference with the local model.

The current Windows environment can load the fine-tuned local adapter on CUDA. However, local Agent 4 smoke tests have returned outputs that do not conform to the required recommendation schema. In particular, the model has produced an object where `recommendations` is a dictionary instead of a list, and has also produced an incomplete response missing required fields. **Local Agent 4 integration remains unverified and must be treated as experimental.**

Do not weaken the Pydantic schema, Agent 3 risk analysis, Agent 5 verification, or evidence checks to make the smoke test pass. If inference or validation fails, return a clear error status and do not present an invalid recommendation as trustworthy.

## Git and artifact policy

Do not commit `.env`, local model weights, copied tokenizer files, optimizer checkpoints, large training datasets, or generated predictions by default. Preserve the adapter and datasets in approved artifact storage and record their checksums/locations in the research handover. Commit source, tests, documentation, small manifests, and selected summary metrics only.

Stage explicit paths and review `git diff --cached` before committing and pushing from the developer's authenticated workstation.
