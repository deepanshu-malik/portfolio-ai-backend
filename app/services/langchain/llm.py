"""LLM and embeddings setup for LangChain."""

from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import settings
from app.services.langchain.callbacks import token_handler


@lru_cache()
def get_llm(
    model: str = None,
    temperature: float = 0.7,
    streaming: bool = False,
) -> ChatOpenAI:
    """Get configured ChatOpenAI instance with token tracking."""
    return ChatOpenAI(
        model=model or settings.openai_model,
        temperature=temperature,
        api_key=settings.openai_api_key,
        streaming=streaming,
        callbacks=[token_handler],
    )


@lru_cache()
def get_embeddings() -> OpenAIEmbeddings:
    """Get configured OpenAI embeddings."""
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )
