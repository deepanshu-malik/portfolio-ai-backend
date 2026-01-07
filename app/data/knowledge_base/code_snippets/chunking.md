# Document Chunking Strategies

## Overview
Strategies for splitting large documents into smaller chunks for embedding and retrieval in RAG systems.

## Problem Solved
Large documents don't fit in embedding models or LLM context windows. Need to split while preserving semantic meaning.

## Three Strategies Implemented

### 1. Simple Chunking (Character-based)
```python
def simple_chunking(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```
- Pros: Fast, consistent chunk sizes
- Cons: May split mid-sentence
- Use case: Quick prototyping

### 2. Sentence Chunking (Recommended)
```python
def sentence_chunking(text: str, sentences_per_chunk: int = 5, overlap: int = 1) -> list:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    i = 0
    while i < len(sentences):
        chunk = ' '.join(sentences[i:i + sentences_per_chunk])
        chunks.append(chunk)
        i += sentences_per_chunk - overlap
    return chunks
```
- Pros: Preserves sentence boundaries, semantic
- Cons: Variable chunk sizes
- Use case: Most production RAG systems

### 3. Paragraph Chunking
```python
def paragraph_chunking(text: str) -> list:
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    return paragraphs
```
- Pros: Preserves semantic units
- Cons: Highly variable sizes
- Use case: Well-structured documents, Q&A

## Production Recommendations
- Chunk size: 200-500 words (~256-512 tokens)
- Overlap: 10-20% of chunk size
- Always include metadata (source, chunk_id)
- Sentence chunking is best default choice

## GitHub
https://github.com/deepanshu-malik/genai-sandbox/blob/main/rag/02_chunking_strategies.py
