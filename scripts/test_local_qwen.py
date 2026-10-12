import json
import torch

from agents.recommendation.llm import LocalQwenProvider

print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))

print("Loading local Qwen base model and Agent 4 adapter...")
provider = LocalQwenProvider(max_new_tokens=128)

print("Base model and adapter loaded successfully.")

raw = provider.generate(
    system_prompt=(
        "Return only a valid JSON object with the keys "
        "'status' and 'message'."
    ),
    user_prompt=(
        "Return status as 'ok' and message as "
        "'local model loaded'."
    ),
)

print("Raw output:", raw)
print("Parsed JSON:", json.dumps(json.loads(raw), indent=2))
