# Rate Limiting Implementation

## Overview
Semaphore-based rate limiting for controlling concurrent API calls to avoid hitting OpenAI rate limits.

## Problem Solved
OpenAI has strict rate limits (Free tier: 3 RPM, Paid tier: 500+ RPM). Without rate limiting, batch operations hit 429 errors and waste time on retries.

## Implementation
Uses `asyncio.Semaphore` to limit concurrent requests - like a bouncer at a club controlling how many people enter at once.

## Code Pattern
```python
MAX_CONCURRENT = 2  # Safe for free tier

async def call_with_rate_limit(client: AsyncOpenAI, prompt: str, semaphore: asyncio.Semaphore) -> str:
    async with semaphore:  # Only MAX_CONCURRENT calls run at once
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

async def process_batch(prompts: list[str]) -> list[str]:
    client = AsyncOpenAI()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = [call_with_rate_limit(client, p, semaphore) for p in prompts]
    return await asyncio.gather(*tasks)
```

## Key Learnings
- Set MAX_CONCURRENT based on your tier (free: 2, paid: 50+)
- Even with 100 items, only MAX_CONCURRENT calls happen simultaneously
- Prevents 429 errors while maximizing throughput
- Check limits at: https://platform.openai.com/account/rate-limits

## GitHub
https://github.com/deepanshu-malik/genai-sandbox/blob/main/05_rate_limiting.py
