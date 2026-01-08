"""Token tracking callback handler for LangChain."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)

# Pricing per 1M tokens
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
}


@dataclass
class TokenUsage:
    """Token usage for a single LLM call."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = "gpt-4o-mini"
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def cost(self) -> float:
        pricing = MODEL_PRICING.get(self.model, MODEL_PRICING["gpt-4o-mini"])
        return (
            (self.prompt_tokens / 1_000_000) * pricing["input"] +
            (self.completion_tokens / 1_000_000) * pricing["output"]
        )


class TokenTrackingHandler(BaseCallbackHandler):
    """Callback handler for tracking token usage across LangChain calls."""

    def __init__(self):
        self.usage_log: List[TokenUsage] = []
        self.session_usage: Dict[str, List[TokenUsage]] = {}
        self._current_session: Optional[str] = None

    def set_session(self, session_id: str) -> None:
        """Set current session for tracking."""
        self._current_session = session_id

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Track tokens when LLM call completes."""
        if not response.llm_output:
            return

        token_usage = response.llm_output.get("token_usage", {})
        model = response.llm_output.get("model_name", "gpt-4o-mini")

        usage = TokenUsage(
            prompt_tokens=token_usage.get("prompt_tokens", 0),
            completion_tokens=token_usage.get("completion_tokens", 0),
            model=model,
        )

        self.usage_log.append(usage)

        if self._current_session:
            if self._current_session not in self.session_usage:
                self.session_usage[self._current_session] = []
            self.session_usage[self._current_session].append(usage)

        logger.info(
            f"LangChain tokens: {usage.total_tokens} "
            f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens}) "
            f"Cost: ${usage.cost:.6f}"
        )

    def get_session_stats(self, session_id: str) -> Dict:
        """Get aggregated stats for a session."""
        usages = self.session_usage.get(session_id, [])
        if not usages:
            return {"total_tokens": 0, "total_cost": 0, "request_count": 0}

        return {
            "total_tokens": sum(u.total_tokens for u in usages),
            "prompt_tokens": sum(u.prompt_tokens for u in usages),
            "completion_tokens": sum(u.completion_tokens for u in usages),
            "total_cost": sum(u.cost for u in usages),
            "request_count": len(usages),
        }

    def get_total_stats(self) -> Dict:
        """Get total stats across all requests."""
        if not self.usage_log:
            return {"total_tokens": 0, "total_cost": 0, "request_count": 0}

        return {
            "total_tokens": sum(u.total_tokens for u in self.usage_log),
            "prompt_tokens": sum(u.prompt_tokens for u in self.usage_log),
            "completion_tokens": sum(u.completion_tokens for u in self.usage_log),
            "total_cost": sum(u.cost for u in self.usage_log),
            "request_count": len(self.usage_log),
        }


# Global handler instance
token_handler = TokenTrackingHandler()
