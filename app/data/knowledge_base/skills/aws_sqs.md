# AWS SQS Patterns

## Proficiency: Advanced

## Overview
AWS Simple Queue Service for decoupled, scalable message processing. I use SQS extensively for async workflows in production systems.

## Experience
- Built queue-based architectures for high-volume message processing
- FIFO queues for ordered, exactly-once processing
- Webhook processing with dedicated queues
- Batch operations for efficiency

## Patterns I Implement

### Queue Types
| Type | Use Case |
|------|----------|
| **Standard** | High throughput, at-least-once delivery |
| **FIFO** | Ordered processing, exactly-once, deduplication |

### Producer Pattern
```python
# Batch sending for efficiency (max 10 per call)
sqs.send_message_batch(
    QueueUrl=queue_url,
    Entries=[
        {
            "Id": str(uuid4()),
            "MessageBody": json.dumps(data),
            "MessageGroupId": batch_id,  # FIFO ordering
            "MessageDeduplicationId": unique_id,  # Prevent duplicates
        }
        for data in batch
    ]
)
```

### Consumer Pattern
```python
# Long polling reduces costs
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20,  # Long poll
    VisibilityTimeout=300,  # Processing window
)
```

### Error Handling Strategy
- **Visibility Timeout**: Message reappears if not deleted
- **Dead Letter Queue**: After N failures, move to DLQ
- **Graceful Degradation**: Log and continue on individual failures

## Architecture Decisions

### When to Use SQS
- Decoupling services (API → Worker)
- Handling traffic spikes (queue absorbs burst)
- Retry logic (automatic via visibility timeout)
- Async processing (don't block API responses)

### FIFO vs Standard
- Use FIFO when order matters or duplicates are problematic
- Use Standard for higher throughput when order doesn't matter

## Projects Using SQS
- Communication Platform: Message sending queue, webhook processing queue
- Document Dispatch: PDF generation queue with FIFO ordering
