import json
import traceback
from pathlib import Path

from agents.recommendation.llm.local_qwen_provider import LocalQwenProvider

provider = LocalQwenProvider(max_new_tokens=256)

system_prompt = Path(
    "agents/recommendation/prompts/recommendation_v1.txt"
).read_text(encoding="utf-8")

user_prompt = json.dumps({
    "project_id": "LOCAL-SMOKE-002",
    "dependencies": [{
        "package_name": "numpy",
        "ecosystem": "pypi",
        "version_constraint": None,
        "source_file": "requirements.txt",
        "registry_status": "verified",
        "risk_score": 0,
        "risk_level": "low",
        "signals": [],
    }],
}, indent=2)

try:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

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
            max_new_tokens=256,
            do_sample=False,
            pad_token_id=provider.tokenizer.eos_token_id,
        )

    generated_ids = output_ids[0, inputs["input_ids"].shape[1]:]
    print("Generated token count:", len(generated_ids))
    print("Generated token IDs:", generated_ids.tolist())
    print("Decoded output repr:", repr(
        provider.tokenizer.decode(
            generated_ids,
            skip_special_tokens=False,
        )
    ))
    print("Decoded output:", provider.tokenizer.decode(
        generated_ids,
        skip_special_tokens=True,
    ))

except Exception:
    traceback.print_exc()
