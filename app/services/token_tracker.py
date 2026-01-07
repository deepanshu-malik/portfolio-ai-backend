"""Token usage and cost tracking for LLM calls."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Pricing per 1M tokens (as of 2024)
MODEL_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
}


@dataclass
class TokenUsage:
    """Token usage for a single request."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = "gpt-4o-mini"
    timestamp: datetime = field(default_factory=datetime.now)
    request_type: str = "chat"  # chat, intent, embedding

    @property
    def cost(self) -> float:
        """Calculate cost in USD."""
        pricing = MODEL_PRICING.get(self.model, MODEL_PRICING["gpt-4o-mini"])
        input_cost = (self.prompt_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.completion_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost


class TokenTracker:
    """
    Tracks token usage and costs across requests.
    
    Features:
    - Per-request tracking
    - Session aggregation
    - Cost calculation
    """

    def __init__(self):
        """Initialize the token tracker."""
        self.usage_log: List[TokenUsage] = []
        self.session_usage: Dict[str, List[TokenUsage]] = {}

    def track(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "gpt-4o-mini",
        request_type: str = "chat",
        session_id: Optional[str] = None,
    ) -> TokenUsage:
        """
        Track token usage for a request.

        Args:
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            model: Model used
            request_type: Type of request
            session_id: Optional session ID for grouping

        Returns:
            TokenUsage object
        """
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=model,
            request_type=request_type,
        )

        self.usage_log.append(usage)

        if session_id:
            if session_id not in self.session_usage:
                self.session_usage[session_id] = []
            self.session_usage[session_id].append(usage)

        logger.info(
            f"Token usage: {usage.total_tokens} tokens "
            f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens}) "
            f"Cost: ${usage.cost:.6f}"
        )

        return usage

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
            "by_type": self._group_by_type(usages),
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
            "by_type": self._group_by_type(self.usage_log),
        }

    def _group_by_type(self, usages: List[TokenUsage]) -> Dict:
        """Group usage by request type."""
        by_type = {}
        for u in usages:
            if u.request_type not in by_type:
                by_type[u.request_type] = {"tokens": 0, "cost": 0, "count": 0}
            by_type[u.request_type]["tokens"] += u.total_tokens
            by_type[u.request_type]["cost"] += u.cost
            by_type[u.request_type]["count"] += 1
        return by_type


# Global tracker instance
token_tracker = TokenTracker()
