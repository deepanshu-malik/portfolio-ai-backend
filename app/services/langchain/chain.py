"""Conversational chain using LangChain."""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.services.langchain.llm import get_llm
from app.services.langchain.retriever import LangChainHybridRetriever
from app.services.langchain.callbacks import token_handler
from app.prompts.system_prompts import get_system_prompt

logger = logging.getLogger(__name__)


class ConversationalChain:
    """RAG chain with conversation memory."""

    def __init__(self):
        self.retriever = LangChainHybridRetriever()
        self.llm = get_llm()
        self.conversations: Dict[str, List] = {}

    def _get_history(self, session_id: str) -> List:
        """Get conversation history for session."""
        return self.conversations.get(session_id, [])

    def _add_to_history(self, session_id: str, human: str, ai: str) -> None:
        """Add exchange to conversation history."""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        self.conversations[session_id].extend([
            HumanMessage(content=human),
            AIMessage(content=ai),
        ])
        # Keep last 10 exchanges
        if len(self.conversations[session_id]) > 20:
            self.conversations[session_id] = self.conversations[session_id][-20:]

    async def invoke(
        self,
        query: str,
        session_id: str,
        intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate response with RAG."""
        # Retrieve context
        docs = await self.retriever.retrieve(query, intent=intent)
        context = "\n\n".join(d["content"] for d in docs) if docs else ""

        # Build prompt
        system_prompt = get_system_prompt(intent or "general")
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ])

        # Get history
        history = self._get_history(session_id)

        # Generate response
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "context": context,
            "question": query,
            "history": history,
        })

        # Update history
        self._add_to_history(session_id, query, response.content)

        return {
            "response": response.content,
            "sources": [d.get("source", "") for d in docs],
            "intent": intent,
        }

    async def stream(
        self,
        query: str,
        session_id: str,
        intent: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """Stream response with RAG."""
        docs = await self.retriever.retrieve(query, intent=intent)
        context = "\n\n".join(d["content"] for d in docs) if docs else ""

        system_prompt = get_system_prompt(intent or "general")
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ])

        history = self._get_history(session_id)
        chain = prompt | self.llm

        full_response = ""
        async for chunk in chain.astream({
            "context": context,
            "question": query,
            "history": history,
        }):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            full_response += content
            yield content

        self._add_to_history(session_id, query, full_response)

    def get_token_stats(self) -> Dict[str, Any]:
        """Get token usage statistics."""
        return token_handler.get_stats()

    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for session."""
        self.conversations.pop(session_id, None)
