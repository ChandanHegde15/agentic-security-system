
"""Local Qwen + PEFT LoRA provider for Agent 4."""

import json
import os
from pathlib import Path

from .base import LLMProvider


class LocalQwenProvider(LLMProvider):
    """Run the fine-tuned Qwen model locally instead of using an API."""

    def __init__(
        self,
        adapter_path: str | Path | None = None,
        base_model: str | None = None,
        max_new_tokens: int = 1200,
    ) -> None:
        self.adapter_path = Path(
            adapter_path
            or os.getenv(
                "AGENT4_ADAPTER_PATH",
                "models/agent4_recovered_adapters/final_adapter",
            )
        ).resolve()

        self.base_model = (
            base_model
            or os.getenv(
                "AGENT4_BASE_MODEL",
                "Qwen/Qwen2.5-0.5B-Instruct",
            )
        )
        self.max_new_tokens = max_new_tokens

        if not (self.adapter_path / "adapter_config.json").is_file():
            raise FileNotFoundError(
                f"Adapter config not found: "
                f"{self.adapter_path / 'adapter_config.json'}"
            )

        if not any(
            (self.adapter_path / filename).is_file()
            for filename in (
                "adapter_model.safetensors",
                "adapter_model.bin",
            )
        ):
            raise FileNotFoundError(
                f"Adapter weights not found in {self.adapter_path}"
            )

        # Heavy dependencies are imported only when this provider is used.
        try:
            import torch
            from peft import PeftModel
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
            )
        except ImportError as exc:
            raise ImportError(
                "Local Qwen requires torch, transformers, and peft. "
                "Install the compatible dependencies first."
            ) from exc

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(self.adapter_path),
            local_files_only=True,
        )

        # Use the local Hugging Face cache for the base model.
        # If it is not cached, download it separately before running offline.
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            torch_dtype=torch.float32,
            local_files_only=True,
        )

        self.model = PeftModel.from_pretrained(
            self.model,
            str(self.adapter_path),
            is_trainable=False,
            local_files_only=True,
        )

        self.model.eval()
        self.device = next(self.model.parameters()).device

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        rendered_prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(
            rendered_prompt,
            return_tensors="pt",
        ).to(self.device)

        with self.torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode only newly generated tokens, not the input prompt.
        new_tokens = output_ids[0, inputs["input_ids"].shape[1]:]
        response = self.tokenizer.decode(
            new_tokens,
            skip_special_tokens=True,
        ).strip()

        if not response:
            raise RuntimeError("Local Qwen returned an empty response.")

        # Fail early for malformed JSON; RecommendationAgent performs
        # the authoritative Pydantic and evidence validation afterward.
        try:
            json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Local Qwen returned invalid JSON. "
                "Review the prompt and model output."
            ) from exc

        return response
