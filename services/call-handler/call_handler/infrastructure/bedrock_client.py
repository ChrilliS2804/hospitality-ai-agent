"""Amazon Bedrock client wrapper for Claude invocation.

Handles:
- Model invocation with retry and error handling
- Conversation history formatting (messages array)
- Structured JSON response parsing
- Token usage tracking for cost monitoring
"""

from __future__ import annotations

import json
import os
from typing import Any

from botocore.exceptions import ClientError

from hospitality_shared.domain.exceptions import InfrastructureError
from hospitality_shared.infrastructure.aws.clients import get_bedrock_runtime_client
from hospitality_shared.infrastructure.logging.logger import get_logger
from hospitality_shared.infrastructure.tracing.tracer import traced_subsegment

logger = get_logger("call-handler")

# Model ID — configurable via environment variable
_MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID",
    "anthropic.claude-haiku-4-5-20251001-v1:0",
)

# Max tokens for response generation
_MAX_TOKENS = int(os.environ.get("BEDROCK_MAX_TOKENS", "1024"))

# Temperature — lower = more deterministic (good for slot extraction)
_TEMPERATURE = float(os.environ.get("BEDROCK_TEMPERATURE", "0.3"))


class BedrockConversationClient:
    """Client for invoking Claude via Amazon Bedrock for conversation handling.

    Usage::

        client = BedrockConversationClient()
        response = client.converse(
            system_prompt="You are a restaurant assistant...",
            messages=[
                {"role": "user", "content": "Ich moechte reservieren"},
            ],
        )
        # response = {"role": "assistant", "content": "..."}
    """

    def __init__(self) -> None:
        self._client = get_bedrock_runtime_client()
        self._model_id = _MODEL_ID

    def converse(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Invoke Claude with a system prompt and message history.

        Args:
            system_prompt: The system-level instruction (agent persona, constraints).
            messages: List of {"role": "user"|"assistant", "content": "..."} dicts.

        Returns:
            Dict with keys:
                - "content": The assistant's response text
                - "input_tokens": Number of input tokens used
                - "output_tokens": Number of output tokens used
                - "stop_reason": Why generation stopped

        Raises:
            InfrastructureError: If Bedrock invocation fails.
        """
        with traced_subsegment("bedrock_converse", model=self._model_id):
            try:
                response = self._client.converse(
                    modelId=self._model_id,
                    system=[{"text": system_prompt}],
                    messages=[
                        {"role": m["role"], "content": [{"text": m["content"]}]}
                        for m in messages
                    ],
                    inferenceConfig={
                        "maxTokens": _MAX_TOKENS,
                        "temperature": _TEMPERATURE,
                    },
                )
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code", "Unknown")
                logger.error(
                    "Bedrock converse failed",
                    error_code=error_code,
                    model_id=self._model_id,
                )
                raise InfrastructureError(
                    f"Bedrock invocation failed: {error_code}",
                    cause=exc,
                ) from exc

        # Extract response
        output = response.get("output", {})
        content_blocks = output.get("message", {}).get("content", [])
        content_text = content_blocks[0].get("text", "") if content_blocks else ""

        # Token usage
        usage = response.get("usage", {})
        input_tokens = usage.get("inputTokens", 0)
        output_tokens = usage.get("outputTokens", 0)

        logger.info(
            "Bedrock response received",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            stop_reason=response.get("stopReason", "unknown"),
        )

        return {
            "content": content_text,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "stop_reason": response.get("stopReason", "unknown"),
        }

    def parse_structured_response(self, raw_content: str) -> dict[str, Any]:
        """Parse Claude's response as structured JSON.

        The system prompt instructs Claude to respond with JSON containing:
        - intent: str
        - slots: dict
        - response_text: str
        - next_action: str (continue | confirm | complete | handoff)

        If parsing fails, returns a fallback with the raw text as response_text.
        """
        # Try to extract JSON from the response
        content = raw_content.strip()

        # Handle case where Claude wraps JSON in markdown code blocks
        if "```json" in content:
            start = content.index("```json") + 7
            end = content.index("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.index("```") + 3
            end = content.index("```", start)
            content = content[start:end].strip()

        try:
            parsed = json.loads(content)
            # Validate expected keys exist
            if "response_text" not in parsed:
                parsed["response_text"] = content
            return parsed  # type: ignore[no-any-return]
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "Failed to parse structured response, using raw text",
                raw_content_preview=content[:200],
            )
            return {
                "intent": "UNKNOWN",
                "slots": {},
                "response_text": raw_content,
                "next_action": "continue",
            }
