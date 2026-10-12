
import json
import torch

from agents.recommendation.agent import RecommendationAgent
from agents.recommendation.llm.local_qwen_provider import LocalQwenProvider

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

print("CUDA available:", torch.cuda.is_available())
print("Loading fine-tuned Agent 4...")
provider = LocalQwenProvider(max_new_tokens=512)
agent = RecommendationAgent(llm_provider=provider)

print("Calling Agent 4 with synthetic Agent 3 evidence...")
result = agent.recommend(risk_result)

output = result.model_dump(mode="json")
print(json.dumps(output, indent=2))

assert output["project_id"] == risk_result["project_id"]
assert len(output["recommendations"]) == len(risk_result["dependencies"])

allowed_actions = {
    "no_action",
    "monitor",
    "investigate",
    "replace",
    "review",
    "insufficient_evidence",
}

for recommendation in output["recommendations"]:
    assert recommendation["action"] in allowed_actions
    assert recommendation["suggested_version"] is None
    supplied_types = {
        signal["type"]
        for dependency in risk_result["dependencies"]
        if dependency["package_name"] == recommendation["package_name"]
        for signal in dependency["signals"]
    }
    assert set(recommendation["evidence_referenced"]).issubset(supplied_types)

print("\nPASS: Agent 4 output passed schema and evidence validation.")
