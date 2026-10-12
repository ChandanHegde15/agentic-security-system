import json
from pathlib import Path

from agents.recommendation.llm.local_qwen_provider import LocalQwenProvider

dataset_path = Path(
    "research/datasets/agent4_sft/v1.0/source/"
    "agent4_finetuning_dataset_1000_revised.json"
)
data = json.loads(dataset_path.read_text(encoding="utf-8-sig"))
example = next(x for x in data["examples"] if x["example_id"] == "FT-0001")

# Critical: do not feed the assistant's target answer into the model.
messages = [
    message for message in example["messages"]
    if message["role"] in ("system", "user")
]

print("Testing:", example["example_id"])
print("Input roles:", [m["role"] for m in messages])

provider = LocalQwenProvider(max_new_tokens=512)

prompt = provider.tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
)
inputs = provider.tokenizer(
    prompt,
    return_tensors="pt",
).to(provider.device)

with provider.torch.inference_mode():
    output_ids = provider.model.generate(
        **inputs,
        max_new_tokens=512,
        do_sample=False,
        pad_token_id=provider.tokenizer.eos_token_id,
    )

generated = output_ids[0, inputs["input_ids"].shape[1]:]
raw = provider.tokenizer.decode(generated, skip_special_tokens=True)

print("\n--- GENERATED OUTPUT ---")
print(raw)

try:
    parsed = json.loads(raw)
    print("\nTop-level keys:", list(parsed.keys()))
    print("Has expected schema:", set(parsed) == {"project_id", "recommendations"})
except json.JSONDecodeError as exc:
    print("\nInvalid JSON:", exc)

print("\n--- REFERENCE TARGET (not sent to model) ---")
print(json.dumps(example["ground_truth"]["agent_4_target"], indent=2))
