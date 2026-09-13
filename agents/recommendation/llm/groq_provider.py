import json
import os

from groq import Groq

from .base import LLMProvider

class GroqProvider(LLMProvider):

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:

        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is not set."
            )

        self.model = (
            model
            or os.getenv(
                "AGENT4_MODEL",
                "openai/gpt-oss-20b",
            )
        )

        self.client = Groq(api_key=self.api_key)

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "agent4_recommendation",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string"
                            },
                            "recommendations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "package_name": {
                                            "type": "string"
                                        },
                                        "action": {
                                            "type": "string",
                                            "enum": [
                                                "no_action",
                                                "monitor",
                                                "investigate",
                                                "replace",
                                                "review",
                                                "insufficient_evidence",
                                            ],
                                        },
                                        "suggested_package": {
                                            "type": [
                                                "string",
                                                "null",
                                            ]
                                        },
                                        "suggested_version": {
                                            "type": [
                                                "string",
                                                "null",
                                            ]
                                        },
                                        "confidence": {
                                            "type": "number"
                                        },
                                        "reasoning": {
                                            "type": "string"
                                        },
                                        "evidence_referenced": {
                                            "type": "array",
                                            "items": {
                                                "type": "string"
                                            },
                                        },
                                        "conditional": {
                                            "type": "boolean"
                                        },
                                    },
                                    "required": [
                                        "package_name",
                                        "action",
                                        "suggested_package",
                                        "suggested_version",
                                        "confidence",
                                        "reasoning",
                                        "evidence_referenced",
                                        "conditional",
                                    ],
                                    "additionalProperties": False,
                                },
                            },
                        },
                        "required": [
                            "project_id",
                            "recommendations",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "Groq returned an empty response."
            )

        json.loads(content)

        return content
