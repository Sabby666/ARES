import json
import logging
import httpx
import asyncio
from typing import Dict, Any, List
from .provider import LLMProvider
from .schemas import AnalysisResultSchema, ReasoningResultSchema
from app.core.config import settings
from .prompts.analyzer_prompt import (
    ANALYZER_SYSTEM_PROMPT,
    REASONER_SYSTEM_PROMPT,
    REASONER_USER_PROMPT_TEMPLATE,
    build_analyzer_user_prompt,
)

logger = logging.getLogger(__name__)

class OmniRouteProvider(LLMProvider):
    """OpenAI-compatible LLM Provider using httpx."""

    def __init__(self):
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.api_key = settings.LLM_API_KEY
        self.model = settings.LLM_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.max_retries = 2

    async def _call_api(self, system_prompt: str, user_prompt: str, response_format: Dict = None) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=float(settings.LLM_TIMEOUT_SECONDS)) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    logger.info(f"Sending LLM request to {self.base_url} using model {self.model} (Attempt {attempt + 1})")
                    
                    request = client.build_request(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers=self.headers,
                        json=payload
                    )
                    response = await client.send(request, stream=True)
                    
                    if response.status_code != 200:
                        await response.aclose()
                        logger.error(f"LLM Provider HTTP error: {response.status_code}")
                        if response.status_code in [401, 403, 400]:
                            raise RuntimeError(f"LLM API fatal error: {response.status_code}")
                        if attempt == self.max_retries:
                            raise RuntimeError(f"LLM API returned status {response.status_code}")
                        # Force a retry
                        raise httpx.HTTPStatusError(f"HTTP {response.status_code}", request=request, response=response)

                    content_type = response.headers.get("content-type", "")
                    if "text/event-stream" in content_type:
                        logger.info("Received SSE response, parsing stream...")
                        full_content = ""
                        async for line in response.aiter_lines():
                            line = line.strip()
                            if not line or line.startswith(":"):
                                continue
                            if line == "data: [DONE]":
                                logger.info("SSE stream completed")
                                break
                            if line.startswith("data: "):
                                try:
                                    chunk = json.loads(line[6:])
                                    choices = chunk.get("choices", [])
                                    if choices:
                                        delta = choices[0].get("delta", {})
                                        if "content" in delta and isinstance(delta["content"], str):
                                            full_content += delta["content"]
                                except json.JSONDecodeError:
                                    logger.warning("Malformed SSE JSON payload")
                        await response.aclose()
                        
                        if not full_content:
                            raise RuntimeError("Empty or invalid SSE response")
                        
                        logger.info("LLM response validated (SSE)")
                        return full_content
                    else:
                        await response.aread()
                        data = response.json()
                        logger.info("LLM response validated (JSON)")
                        return data["choices"][0]["message"]["content"]
                        
                except httpx.HTTPStatusError:
                    # Logged above
                    pass
                except httpx.RequestError as e:
                    logger.error(f"LLM Provider connection error: {str(e)}")
                    if attempt == self.max_retries:
                        raise RuntimeError("LLM API connection failed")
                except Exception as e:
                    if isinstance(e, RuntimeError):
                        raise
                    logger.error(f"LLM Provider unexpected error: {str(e)}")
                    if attempt == self.max_retries:
                        raise RuntimeError("LLM API request failed")
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
            
            raise RuntimeError("LLM Provider failed after max retries")

    async def analyze_recon_data(self, recon_data: Dict[str, Any]) -> AnalysisResultSchema:
        # Use the structured per-section prompt builder (Phase 10)
        user_prompt = build_analyzer_user_prompt(recon_data)
        schema_str = json.dumps(AnalysisResultSchema.model_json_schema(), indent=2)
        user_prompt += (
            f"\n\nIMPORTANT: You must return ONLY a JSON object that perfectly "
            f"validates against this JSON schema:\n{schema_str}"
        )
        try:
            result_str = await self._call_api(
                ANALYZER_SYSTEM_PROMPT,
                user_prompt,
                response_format={"type": "json_object"}
            )
            result_json = json.loads(result_str)
            return AnalysisResultSchema.model_validate(result_json)
        except Exception as e:
            logger.error(f"Failed to parse LLM response for analysis: {str(e)}")
            raise

    async def reason_about_findings(self, findings: List[Dict[str, Any]], recon_data: Dict[str, Any]) -> ReasoningResultSchema:
        user_prompt = REASONER_USER_PROMPT_TEMPLATE.format(
            recon_data=json.dumps(recon_data, indent=2),
            findings=json.dumps(findings, indent=2)
        )
        schema_str = json.dumps(ReasoningResultSchema.model_json_schema(), indent=2)
        user_prompt += f"\n\nIMPORTANT: You must return ONLY a JSON object that perfectly validates against this JSON schema:\n{schema_str}"
        try:
            result_str = await self._call_api(
                REASONER_SYSTEM_PROMPT,
                user_prompt,
                response_format={"type": "json_object"}
            )
            result_json = json.loads(result_str)
            return ReasoningResultSchema.model_validate(result_json)
        except Exception as e:
            logger.error(f"Failed to parse LLM response for reasoning: {str(e)}")
            raise

    async def plan_next_action(self, state: Dict[str, Any]) -> "PentestActionSchema":
        from .prompts.vapt_prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT_TEMPLATE
        from .schemas import PentestActionSchema

        user_prompt = PLANNER_USER_PROMPT_TEMPLATE.format(
            target=state.get("target", "Unknown"),
            actions_taken=state.get("actions_taken", 0),
            max_actions=state.get("max_actions", 10),
            status=state.get("status", "IN_PROGRESS"),
            attack_surfaces=json.dumps(state.get("attack_surfaces", []), indent=2),
            findings=json.dumps(state.get("findings", []), indent=2),
            past_actions=json.dumps(state.get("past_actions", []), indent=2)
        )
        schema_str = json.dumps(PentestActionSchema.model_json_schema(), indent=2)
        user_prompt += f"\n\nIMPORTANT: You must return ONLY a JSON object that perfectly validates against this JSON schema:\n{schema_str}"
        
        try:
            result_str = await self._call_api(
                PLANNER_SYSTEM_PROMPT,
                user_prompt,
                response_format={"type": "json_object"}
            )
            result_json = json.loads(result_str)
            return PentestActionSchema.model_validate(result_json)
        except Exception as e:
            logger.error(f"Failed to parse LLM response for planner: {str(e)}")
            raise

    async def evaluate_observation(self, action: Dict[str, Any], result: Dict[str, Any], state: Dict[str, Any]) -> "ObservationResultSchema":
        from .prompts.vapt_prompts import OBSERVATION_SYSTEM_PROMPT, OBSERVATION_USER_PROMPT_TEMPLATE
        from .schemas import ObservationResultSchema

        user_prompt = OBSERVATION_USER_PROMPT_TEMPLATE.format(
            action_type=action.get("action_type", ""),
            capability=action.get("capability", ""),
            target=action.get("target", ""),
            validation_goal=action.get("validation_goal", ""),
            status=result.get("status", ""),
            adapter=result.get("adapter", ""),
            error_message=result.get("error_message", ""),
            structured_data=json.dumps(result.get("structured_data", {}), indent=2),
            output=result.get("output", "")
        )
        schema_str = json.dumps(ObservationResultSchema.model_json_schema(), indent=2)
        user_prompt += f"\n\nIMPORTANT: You must return ONLY a JSON object that perfectly validates against this JSON schema:\n{schema_str}"
        
        try:
            result_str = await self._call_api(
                OBSERVATION_SYSTEM_PROMPT,
                user_prompt,
                response_format={"type": "json_object"}
            )
            result_json = json.loads(result_str)
            return ObservationResultSchema.model_validate(result_json)
        except Exception as e:
            logger.error(f"Failed to parse LLM response for observation: {str(e)}")
            raise
