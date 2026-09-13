import json
from pathlib import Path
from typing import Any
from .llm.base import LLMProvider
from .models import RecommendationResult
from .validation import validate_agent3_input, validate_recommendation

class RecommendationAgent:
    def __init__(self,llm_provider:LLMProvider,prompt_version='recommendation_v1'):
        self.llm_provider=llm_provider
        path=Path(__file__).parent/'prompts'/f'{prompt_version}.txt'
        if not path.exists(): raise FileNotFoundError(f'Prompt not found: {path}')
        self.prompt_version=prompt_version; self.system_prompt=path.read_text(encoding='utf-8')
    def recommend(self,risk_result:dict[str,Any])->RecommendationResult:
        if not isinstance(risk_result,dict): raise TypeError('Agent 3 result must be a dictionary.')
        if 'project_id' not in risk_result: raise ValueError('Agent 3 result is missing project_id.')
        if 'dependencies' not in risk_result: raise ValueError('Agent 3 result is missing dependencies.')
        validate_agent3_input(risk_result)
        raw=self.llm_provider.generate(system_prompt=self.system_prompt,user_prompt=json.dumps(risk_result,indent=2,sort_keys=True))
        try: parsed=json.loads(raw)
        except json.JSONDecodeError as e: raise ValueError('LLM returned invalid JSON.') from e
        try: result=RecommendationResult.model_validate(parsed)
        except Exception as e: raise ValueError('LLM response does not match Agent 4 recommendation schema.') from e
        return validate_recommendation(result,risk_result)
