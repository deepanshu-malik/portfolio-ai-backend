"""LLM-based intent classification service."""

import logging
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.config import settings
from app.services.token_tracker import token_tracker

logger = logging.getLogger(__name__)

INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a portfolio chatbot. Classify the user's message into ONE of these intents:

INTENTS:
- quick_answer: Simple factual questions (contact info, years of experience, location, tech stack)
- project_deepdive: Wants details about a specific project
- experience_deepdive: Wants details about work experience at a company
- code_walkthrough: Wants to see code or implementation details
- skill_assessment: Evaluating fit for a role or assessing skills
- comparison: Comparing two things (projects, technologies, etc.)
- tour: Wants an overview/introduction to the portfolio
- general: Anything else, casual conversation, unclear intent

CONTEXT:
- Current section user is viewing: {current_section}
- Previous topic discussed: {previous_topic}

USER MESSAGE: {message}

Respond with ONLY the intent name, nothing else."""

INTENTS = [
    "quick_answer",
    "project_deepdive", 
    "experience_deepdive",
    "code_walkthrough",
    "skill_assessment",
    "comparison",
    "tour",
    "general",
]


class LLMIntentClassifier:
    """
    LLM-based intent classification for more accurate understanding.
    
    Uses gpt-4o-mini for fast, accurate classification.
    Falls back to regex-based classification on failure.
    """

    def __init__(self):
        """Initialize the LLM intent classifier."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4o-mini"
        
        # Import fallback classifier
        from app.services.intent_classifier import IntentClassifier
        self.fallback_classifier = IntentClassifier()

    async def classify(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Classify intent using LLM.

        Args:
            message: User's message
            context: Optional context with current_section, previous_topic
            session_id: Optional session ID for token tracking

        Returns:
            Classified intent string
        """
        context = context or {}
        
        try:
            prompt = INTENT_CLASSIFICATION_PROMPT.format(
                message=message,
                current_section=context.get("current_section", "none"),
                previous_topic=context.get("previous_topic", "none"),
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=20,
            )

            # Track token usage
            if response.usage:
                token_tracker.track(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    model=self.model,
                    request_type="intent",
                    session_id=session_id,
                )

            intent = response.choices[0].message.content.strip().lower()
            
            # Validate intent
            if intent in INTENTS:
                logger.debug(f"LLM classified intent: {intent}")
                return intent
            else:
                logger.warning(f"LLM returned invalid intent: {intent}, using fallback")
                return self.fallback_classifier.classify(message, context)

        except Exception as e:
            logger.warning(f"LLM intent classification failed: {e}, using fallback")
            return self.fallback_classifier.classify(message, context)

    def get_all_intents(self) -> List[str]:
        """Return list of all possible intents."""
        return INTENTS
