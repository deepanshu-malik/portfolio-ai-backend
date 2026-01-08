# GenAI & LLM Skills

## OpenAI API
- **Proficiency**: Advanced
- **Models**: gpt-4o-mini (primary), text-embedding-3-small
- **Patterns**: Streaming, async calls, rate limiting, retries, error handling
- **Projects**: Portfolio AI Backend, genai-sandbox

I've built production applications using OpenAI API with proper error handling, retry logic, and cost optimization. I understand token limits, pricing, and how to build reliable LLM-powered systems.

## RAG (Retrieval Augmented Generation)
- **Proficiency**: Advanced
- **Experience**: Built complete production pipeline from scratch
- **Components**: Embeddings, chunking, vector search, hybrid retrieval, reranking

My RAG implementation includes:
- Hybrid search (semantic + keyword)
- LLM-based reranking
- Query expansion by intent
- Relevance threshold filtering
- Token-managed context preparation

## Hybrid Search
- **Proficiency**: Advanced
- **Approach**: 70% semantic + 30% keyword scoring
- **Why**: Semantic captures meaning, keyword catches exact matches

I implemented hybrid search to improve retrieval quality over pure semantic search, especially for queries mixing technical terms with natural language.

## LLM Reranking
- **Proficiency**: Intermediate
- **Approach**: Use LLM to reorder top retrieved documents by relevance
- **Trade-off**: Better quality vs additional API call

Reranking improved answer quality by ensuring the most relevant documents appear first in context.

## Token Management
- **Proficiency**: Advanced
- **Tool**: tiktoken
- **Patterns**: Context truncation, history management, cost tracking

I understand context window limits and implement proper token counting to prevent errors and optimize costs. My systems track token usage per request and session.

## Prompt Engineering
- **Proficiency**: Advanced
- **Training**: DeepLearning.AI course
- **Focus**: Intent-specific prompts, structured outputs, persona design

I design system prompts tailored to different intents (quick_answer, project_deepdive, skill_assessment, etc.) for consistent, high-quality outputs.

## ChromaDB
- **Proficiency**: Advanced
- **Experience**: Vector storage, semantic search, metadata filtering
- **Projects**: Portfolio AI Backend, genai-sandbox

I chose ChromaDB for its ease of use, local persistence, and good performance. I use it with OpenAI embeddings for consistent retrieval.

## Embeddings
- **Proficiency**: Advanced
- **Models**: text-embedding-3-small
- **Concepts**: Cosine similarity, chunking strategies, batch embedding

I understand how embeddings work and have implemented semantic search using them. I've experimented with different chunking strategies (simple, sentence, paragraph) and their trade-offs.

## Streaming Responses
- **Proficiency**: Advanced
- **Implementation**: Server-Sent Events (SSE)
- **Benefits**: Better perceived latency, real-time UX

I implement streaming for chat applications to provide immediate feedback to users rather than waiting for complete responses.

## Intent Classification
- **Proficiency**: Advanced
- **Approach**: LLM-based with regex fallback
- **Intents**: 8 categories for routing queries

I use LLM for accurate intent classification with graceful fallback to regex patterns when LLM fails.

## Cost Optimization
- **Proficiency**: Advanced
- **Strategies**: 
  - Use gpt-4o-mini (cost-effective)
  - Token limits prevent runaway costs
  - Per-session tracking for monitoring
  - Batch operations where possible

I track costs per request and implement limits to ensure production systems remain cost-effective.

## What I'm Learning
- **LangChain**: Building agents, tool use patterns
- **Fine-tuning**: Not yet explored, planned for future
- **Multi-modal**: Image understanding with vision models
