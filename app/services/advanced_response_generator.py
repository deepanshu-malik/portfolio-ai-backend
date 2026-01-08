"""Advanced response generator with streaming and token management."""

import asyncio
import logging
import tiktoken
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI, APIError, RateLimitError, APIConnectionError

from app.config import settings
from app.models import Suggestion
from app.prompts.system_prompts import get_system_prompt
from app.prompts.templates import format_context, get_suggestion_templates
from app.services.token_tracker import token_tracker

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]

# Token limits
MAX_CONTEXT_TOKENS = 3000
MAX_HISTORY_TOKENS = 1000
MAX_RESPONSE_TOKENS = 800


class AdvancedResponseGenerator:
    """
    Advanced response generator with streaming and token management.

    Features:
    - Token counting and management
    - Streaming responses
    - Smart context truncation
    - Cost tracking
    - Response quality evaluation
    """

    def __init__(self):
        """Initialize the response generator."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within token limit."""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)

    def _prepare_context(
        self,
        retrieved_docs: List[Dict[str, Any]],
        max_tokens: int = MAX_CONTEXT_TOKENS,
    ) -> str:
        """
        Prepare context from retrieved docs with token management.
        
        Prioritizes higher-scored documents.
        """
        if not retrieved_docs:
            return ""

        # Sort by score (hybrid_score or semantic_score)
        sorted_docs = sorted(
            retrieved_docs,
            key=lambda x: x.get("hybrid_score", x.get("semantic_score", 0)),
            reverse=True,
        )

        context_parts = []
        current_tokens = 0

        for doc in sorted_docs:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            # Format document
            source = metadata.get("source", "")
            category = metadata.get("category", "")
            header = f"[{category.upper()}] {source}" if category else source
            formatted = f"{header}\n{content}" if header else content

            doc_tokens = self.count_tokens(formatted)

            # Check if we can fit this document
            if current_tokens + doc_tokens > max_tokens:
                # Try to fit a truncated version
                remaining_tokens = max_tokens - current_tokens - 50  # Buffer
                if remaining_tokens > 100:
                    truncated = self.truncate_to_tokens(formatted, remaining_tokens)
                    context_parts.append(truncated + "...")
                break

            context_parts.append(formatted)
            current_tokens += doc_tokens

        return "\n\n---\n\n".join(context_parts)

    def _prepare_history(
        self,
        history: List[Dict[str, str]],
        max_tokens: int = MAX_HISTORY_TOKENS,
    ) -> List[Dict[str, str]]:
        """
        Prepare conversation history with token management.
        
        Keeps most recent exchanges that fit within limit.
        """
        if not history:
            return []

        # Start from most recent
        prepared = []
        current_tokens = 0

        for exchange in reversed(history[-10:]):  # Max 10 exchanges
            user_msg = exchange.get("user", "")
            assistant_msg = exchange.get("assistant", "")
            
            exchange_tokens = self.count_tokens(user_msg) + self.count_tokens(assistant_msg)

            if current_tokens + exchange_tokens > max_tokens:
                break

            prepared.insert(0, exchange)
            current_tokens += exchange_tokens

        return prepared

    async def generate(
        self,
        query: str,
        intent: str,
        retrieved_docs: List[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a response with token management.

        Args:
            query: User's question
            intent: Classified intent
            retrieved_docs: Retrieved documents
            history: Conversation history
            session_id: Session ID for tracking
            stream: Whether to stream response

        Returns:
            Response dictionary
        """
        try:
            # Get system prompt
            system_prompt = get_system_prompt(intent)

            # Prepare context with token management
            context = self._prepare_context(retrieved_docs)

            # Prepare history with token management
            prepared_history = self._prepare_history(history or [])

            # Build messages
            messages = [{"role": "system", "content": system_prompt}]

            if context:
                messages.append({
                    "role": "system",
                    "content": f"Relevant information from Deepanshu's portfolio:\n\n{context}",
                })

            # Add history
            for exchange in prepared_history:
                messages.append({"role": "user", "content": exchange.get("user", "")})
                messages.append({"role": "assistant", "content": exchange.get("assistant", "")})

            # Add current query
            messages.append({"role": "user", "content": query})

            # Count input tokens
            input_tokens = sum(self.count_tokens(m["content"]) for m in messages)
            logger.debug(f"Input tokens: {input_tokens}")

            # Generate response
            if stream:
                response_text = await self._stream_response(messages, session_id)
            else:
                response_text, output_tokens = await self._generate_response(messages)
                
                # Track tokens
                token_tracker.track(
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    model=self.model,
                    request_type="chat",
                    session_id=session_id,
                )

            # Generate suggestions
            suggestions = self._generate_suggestions(intent, query, response_text)

            return {
                "response": response_text,
                "suggestions": suggestions,
                "detail_panel": None,
                "token_usage": {
                    "input_tokens": input_tokens,
                    "context_docs": len(retrieved_docs),
                },
            }

        except Exception as e:
            logger.error(f"Response generation error: {e}", exc_info=True)
            return {
                "response": "I apologize, but I encountered an error. Please try again.",
                "suggestions": [],
                "detail_panel": None,
            }

    async def _generate_response(self, messages: List[Dict]) -> tuple[str, int]:
        """Generate response with retry logic."""
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=MAX_RESPONSE_TOKENS,
                )
                
                content = response.choices[0].message.content
                output_tokens = response.usage.completion_tokens
                
                return content, output_tokens

            except (RateLimitError, APIError, APIConnectionError) as e:
                last_error = e
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                logger.warning(f"API error, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)

        raise last_error

    async def _stream_response(
        self,
        messages: List[Dict],
        session_id: Optional[str] = None,
    ) -> str:
        """Stream response for better UX."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=MAX_RESPONSE_TOKENS,
                stream=True,
            )

            full_response = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content

            # Track tokens (estimate for streaming)
            output_tokens = self.count_tokens(full_response)
            input_tokens = sum(self.count_tokens(m["content"]) for m in messages)
            
            token_tracker.track(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                model=self.model,
                request_type="chat_stream",
                session_id=session_id,
            )

            return full_response

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            raise

    async def generate_stream(
        self,
        query: str,
        intent: str,
        retrieved_docs: List[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response.
        
        Yields chunks of text as they're generated.
        """
        system_prompt = get_system_prompt(intent)
        context = self._prepare_context(retrieved_docs)
        prepared_history = self._prepare_history(history or [])

        messages = [{"role": "system", "content": system_prompt}]

        if context:
            messages.append({
                "role": "system",
                "content": f"Relevant information from Deepanshu's portfolio:\n\n{context}",
            })

        for exchange in prepared_history:
            messages.append({"role": "user", "content": exchange.get("user", "")})
            messages.append({"role": "assistant", "content": exchange.get("assistant", "")})

        messages.append({"role": "user", "content": query})

        full_response = ""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=MAX_RESPONSE_TOKENS,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            # Track tokens after streaming completes
            input_tokens = sum(self.count_tokens(m["content"]) for m in messages)
            output_tokens = self.count_tokens(full_response)
            token_tracker.track(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                model=self.model,
                request_type="chat_stream",
                session_id=session_id,
            )

        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            yield "I encountered an error generating the response."

    def _generate_suggestions(
        self,
        intent: str,
        query: str,
        response: str,
    ) -> List[Suggestion]:
        """Generate suggestion chips."""
        templates = get_suggestion_templates(intent)
        return [
            Suggestion(
                label=t["label"],
                action=t["action"],
                target=t["target"],
            )
            for t in templates[:4]
        ]
