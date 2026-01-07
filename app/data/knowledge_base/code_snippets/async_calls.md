# Async LLM Calls

## Overview
Using asyncio to make concurrent LLM API calls instead of sequential ones for dramatically faster batch processing.

## Problem Solved
Sequential API calls are slow. Processing 5 requests sequentially takes ~10 seconds (2s each). Async reduces this to ~2 seconds total.

## Implementation
Uses `AsyncOpenAI` client with `asyncio.gather()` to run multiple calls concurrently.

## Code Pattern
```python
from openai import AsyncOpenAI
import asyncio

client = AsyncOpenAI()

async def classify_text(text: str) -> dict:
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Classify sentiment as positive, negative, or neutral."},
            {"role": "user", "content": text}
        ],
        max_tokens=10
    )
    return {
        "text": text,
        "sentiment": response.choices[0].message.content,
        "tokens": response.usage.total_tokens
    }

async def classify_batch(texts: list[str]) -> list[dict]:
    tasks = [classify_text(text) for text in texts]
    return await asyncio.gather(*tasks)
```

## Performance Comparison
- Sequential: 5 calls × 2s each = 10s
- Async: 5 calls concurrent = ~2s
- Result: 5x faster for batch operations

## Key Learnings
- AsyncOpenAI client is essential for concurrent operations
- asyncio.gather() runs all tasks simultaneously
- Combine with rate limiting for production use
- Essential for handling multiple concurrent users

## GitHub
https://github.com/deepanshu-malik/genai-sandbox/blob/main/04_async_calls.py
