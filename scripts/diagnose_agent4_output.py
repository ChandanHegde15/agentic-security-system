import json
from pathlib import Path

from agents.recommendation.llm.local_qwen_provider import LocalQwenProvider

prompt_path = Path("agents/recommendation/prompts/recommendation_v1.txt")
system_prompt = prompt_path.read_text(encoding="utf-8")

risk_result = {
    "project_id": "LOCAL-SMOKE-001",
    "dependencies": [
        {
            "package_name": "request",
            "ecosystem": "pypi",
            "version_constraint": None,
            "source_file": "requirements.txt",
            "registry_status": "not_found",
            "risk_score": 70,
            "risk_level": "high",
            "signals": [
                {
                    "type": "not_found",
                    "weight": 50,
                    "evidence": "Package was not found in the registry.",
                    "reference_package": None,
                    "similarity": None,
                },
                {
                    "type": "name_similarity",
                    "weight": 20,
                    "evidence": "Name similarity to the supplied reference package.",
                    "reference_package": "requests",
                    "similarity": 0.875,
                },
            ],
        }
    ],
}

provider = LocalQwenProvider(max_new_tokens=512)

print("\n--- TOKENIZER CHAT TEMPLATE (first 1000 chars) ---")
print(provider.tokenizer.chat_template[:1000])

print("\n--- SYSTEM PROMPT ---")
print(system_prompt)

print("\n--- RAW MODEL OUTPUT ---")
try:
    raw = provider.generate(
        system_prompt=system_prompt,
        user_prompt=json.dumps(risk_result, indent=2, sort_keys=True),
    )
    print(raw)
except Exception as exc:
    print(type(exc).__name__ + ":", exc)
    raise
