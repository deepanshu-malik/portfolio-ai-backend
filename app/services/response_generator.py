"""Response generation service using OpenAI API."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError

from app.config import settings
from app.models import Suggestion
from app.prompts.system_prompts import get_system_prompt
from app.prompts.templates import format_context, get_suggestion_templates

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff


class ResponseGenerator:
    """
    Generates responses using OpenAI API with RAG context.

    Features:
    - Intent-aware system prompts
    - Context injection from retrieved documents
    - Suggestion generation
    - Conversation history handling
    - Retry logic with exponential backoff
    """

    def __init__(self):
        """Initialize the response generator."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def generate(
        self,
        query: str,
        intent: str,
        retrieved_docs: List[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a response for a user query.

        Args:
            query: The user's question
            intent: Classified intent
            retrieved_docs: Documents retrieved from RAG
            history: Conversation history

        Returns:
            Dictionary with response, suggestions, and optional detail_panel
        """
        try:
            # Get system prompt for intent
            system_prompt = get_system_prompt(intent)

            # Format context from retrieved documents
            context = format_context(retrieved_docs)

            # Build messages
            messages = [{"role": "system", "content": system_prompt}]

            # Add context if available
            if context:
                messages.append(
                    {
                        "role": "system",
                        "content": f"Relevant information from Deepanshu's portfolio:\n\n{context}",
                    }
                )

            # Add conversation history (last 5 exchanges)
            if history:
                for exchange in history[-5:]:
                    messages.append({"role": "user", "content": exchange.get("user", "")})
                    messages.append(
                        {"role": "assistant", "content": exchange.get("assistant", "")}
                    )

            # Add current query
            messages.append({"role": "user", "content": query})

            # Generate response with retry logic
            response_text = await self._call_openai_with_retry(messages)

            # Generate suggestions based on intent and response
            suggestions = self._generate_suggestions(intent, query, response_text)

            # Check if detail panel should be triggered
            detail_panel = self._check_detail_panel(intent, response_text)

            return {
                "response": response_text,
                "suggestions": suggestions,
                "detail_panel": detail_panel,
            }

        except Exception as e:
            logger.error(f"Response generation error: {e}", exc_info=True)
            return {
                "response": "I apologize, but I encountered an error generating a response. Please try again.",
                "suggestions": [],
                "detail_panel": None,
            }

    async def _call_openai_with_retry(self, messages: List[Dict]) -> str:
        """Call OpenAI API with exponential backoff retry."""
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=800,
                )
                return response.choices[0].message.content

            except RateLimitError as e:
                last_error = e
                delay = RETRY_DELAYS[attempt] if attempt < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
                logger.warning(f"Rate limited, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(delay)

            except (APIError, APIConnectionError) as e:
                last_error = e
                delay = RETRY_DELAYS[attempt] if attempt < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
                logger.warning(f"API error: {e}, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(delay)

        logger.error(f"All retries failed: {last_error}")
        raise last_error

    def _generate_suggestions(
        self,
        intent: str,
        query: str,
        response: str,
    ) -> List[Suggestion]:
        """Generate relevant suggestion chips based on context."""
        suggestions = []
        templates = get_suggestion_templates(intent)

        for template in templates[:4]:  # Max 4 suggestions
            suggestions.append(
                Suggestion(
                    label=template["label"],
                    action=template["action"],
                    target=template["target"],
                )
            )

        return suggestions

    def _check_detail_panel(
        self,
        intent: str,
        response: str,
    ) -> Optional[Dict[str, Any]]:
        """Check if response should trigger a detail panel."""
        # For now, return None - detail panels are triggered by suggestion clicks
        # In future, could auto-trigger for code-heavy responses
        return None


class FallbackResponseGenerator:
    """
    Fallback response generator when OpenAI API is not available.
    Uses pre-defined responses based on intent and keywords.
    """

    # Pre-defined responses for common queries
    RESPONSES = {
        "quick_answer": {
            "tech stack": "My core stack is Python, FastAPI, and AWS. For databases, I work with MongoDB, MySQL, and OpenSearch. Recently, I've been building with GenAI tools: OpenAI API, LangChain, and ChromaDB.",
            "experience": "I have 4+ years of backend engineering experience, primarily in fintech. Currently, I'm a Senior Software Engineer at Kogta Financial.",
            "location": "I'm based in Sonipat, Haryana, India, and currently work in Gurugram.",
            "default": "I'm Deepanshu Malik, a Senior Backend Engineer with 4+ years of experience. I specialize in Python, FastAPI, and have been working on GenAI applications recently.",
        },
        "project_deepdive": {
            "default": "I'd be happy to tell you more about my projects! I have the genai-sandbox on GitHub, and professional work including a Multi-Channel Communication Platform and Automated Document Dispatch System. What would you like to know more about?"
        },
        "experience_deepdive": {
            "default": "I've worked at several companies: Currently at Kogta Financial as Senior Software Engineer, previously at Capri Global, VoerEir AB, and Tradeindia.com. Which experience would you like to explore?"
        },
        "general": {
            "default": "I'm here to help you learn about Deepanshu's experience, projects, and skills. Feel free to ask about his tech stack, specific projects, or work experience!"
        },
    }

    def generate(
        self,
        query: str,
        intent: str,
    ) -> Dict[str, Any]:
        """Generate a fallback response."""
        query_lower = query.lower()
        intent_responses = self.RESPONSES.get(intent, self.RESPONSES["general"])

        # Try to match keywords
        response = intent_responses.get("default", "")
        for keyword, resp in intent_responses.items():
            if keyword != "default" and keyword in query_lower:
                response = resp
                break

        return {
            "response": response,
            "suggestions": [],
            "detail_panel": None,
        }
