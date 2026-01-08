# Token Management for LLMs

## Overview
Managing token limits is critical for production LLM applications. This pattern ensures context fits within limits while maximizing relevant information.

## Problem Solved
- LLMs have fixed context windows (e.g., 128K for gpt-4o-mini)
- Exceeding limits causes API errors
- Costs scale with tokens - need to optimize
- Must prioritize most relevant content

## Implementation
```python
import tiktoken

class TokenManager:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.encoding = tiktoken.encoding_for_model(model)
        self.limits = {
            "context": 3000,    # Retrieved docs
            "history": 1000,    # Conversation history
            "response": 800,    # Max response tokens
        }
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return self.encoding.decode(tokens[:max_tokens])
    
    def prepare_context(self, docs: list, max_tokens: int = None) -> str:
        """Fit docs into token budget, prioritizing by score"""
        max_tokens = max_tokens or self.limits["context"]
        
        # Sort by relevance score (highest first)
        sorted_docs = sorted(docs, key=lambda x: x.get("score", 0), reverse=True)
        
        context_parts = []
        current_tokens = 0
        
        for doc in sorted_docs:
            doc_tokens = self.count_tokens(doc["content"])
            
            if current_tokens + doc_tokens > max_tokens:
                # Try to fit truncated version
                remaining = max_tokens - current_tokens - 50
                if remaining > 100:
                    truncated = self.truncate_to_tokens(doc["content"], remaining)
                    context_parts.append(truncated + "...")
                break
            
            context_parts.append(doc["content"])
            current_tokens += doc_tokens
        
        return "\n\n---\n\n".join(context_parts)
    
    def prepare_history(self, history: list, max_tokens: int = None) -> list:
        """Keep recent history that fits in budget"""
        max_tokens = max_tokens or self.limits["history"]
        
        prepared = []
        current_tokens = 0
        
        # Start from most recent
        for exchange in reversed(history[-10:]):
            exchange_tokens = (
                self.count_tokens(exchange.get("user", "")) +
                self.count_tokens(exchange.get("assistant", ""))
            )
            
            if current_tokens + exchange_tokens > max_tokens:
                break
            
            prepared.insert(0, exchange)
            current_tokens += exchange_tokens
        
        return prepared
```

## Usage
```python
token_manager = TokenManager()

# Prepare context from retrieved docs
context = token_manager.prepare_context(retrieved_docs)

# Prepare conversation history
history = token_manager.prepare_history(session_history)

# Count before API call
total_input = token_manager.count_tokens(system_prompt + context + query)
```

## Key Patterns
- **Prioritize by Score**: Best docs first, truncate lower-scored ones
- **Reserve Buffers**: Leave room for system prompt and response
- **Recent History**: Keep most recent exchanges, drop older ones
- **Count Before Call**: Validate total tokens before API request

## Cost Tracking
```python
# Track per request
usage = {
    "prompt_tokens": input_tokens,
    "completion_tokens": output_tokens,
    "cost": (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
}
```
