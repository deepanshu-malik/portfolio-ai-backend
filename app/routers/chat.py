"""Chat endpoint for the portfolio AI assistant."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from app.models import ChatRequest, ChatResponse, Suggestion
from app.services.intent_classifier import IntentClassifier
from app.services.response_generator import ResponseGenerator
from app.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
intent_classifier = IntentClassifier()
response_generator = ResponseGenerator()
session_manager = SessionManager()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, chat_request: ChatRequest) -> ChatResponse:
    """
    Process a chat message and return an AI-generated response.

    This endpoint:
    1. Classifies the user's intent
    2. Retrieves relevant context from the knowledge base
    3. Generates an appropriate response
    4. Returns suggestions for follow-up actions
    """
    try:
        message = chat_request.message.strip()
        session_id = chat_request.session_id
        context = chat_request.context

        logger.info(f"Chat request from session {session_id}: {message[:50]}...")

        # Get session history
        session = session_manager.get_session(session_id)
        history = session.get("history", [])

        # Classify intent
        intent = intent_classifier.classify(
            message=message,
            context={
                "current_section": context.current_section if context else None,
                "previous_topic": context.previous_topic if context else None,
                "history": history,
            },
        )
        logger.debug(f"Classified intent: {intent}")

        # Get retriever from app state
        retriever = getattr(request.app.state, "retriever", None)

        # Retrieve relevant documents
        retrieved_docs = []
        if retriever:
            try:
                retrieved_docs = retriever.retrieve(
                    query=message,
                    k=5,
                    intent=intent,
                )
            except Exception as e:
                logger.warning(f"Retrieval failed: {e}")

        # Generate response
        response_data = await response_generator.generate(
            query=message,
            intent=intent,
            retrieved_docs=retrieved_docs,
            history=history,
        )

        # Update session
        session_manager.update_session(
            session_id=session_id,
            message=message,
            response=response_data["response"],
            intent=intent,
        )

        return ChatResponse(
            response=response_data["response"],
            suggestions=response_data.get("suggestions", []),
            detail_panel=response_data.get("detail_panel"),
            intent=intent,
            session_id=session_id,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}",
        )
