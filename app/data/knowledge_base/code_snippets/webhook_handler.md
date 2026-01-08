# Webhook Handler with Idempotent Processing

## Overview
Production pattern for handling high-volume webhooks with idempotent processing and status priority management.

## Problem Solved
Messaging providers send delivery status webhooks that can arrive out of order or be duplicated. Without proper handling:
- Duplicate webhooks cause redundant database updates
- Out-of-order webhooks can downgrade status (DELIVERED → SENT)
- High traffic can overwhelm synchronous processing

## Implementation Pattern

### Status Priority System
```python
from enum import IntEnum

class DeliveryStatus(IntEnum):
    """Status with priority ordering - higher value = more final state"""
    PENDING = 0
    QUEUED = 1
    SENT = 2
    DELIVERED = 3
    READ = 4
    FAILED = 5  # Terminal state

def should_update_status(current: DeliveryStatus, new: DeliveryStatus) -> bool:
    """Only allow status progression, never downgrade"""
    # Failed is terminal - don't overwrite
    if current == DeliveryStatus.FAILED:
        return False
    # Allow progression to higher priority status
    return new > current or new == DeliveryStatus.FAILED
```

### Idempotent Webhook Handler
```python
async def handle_webhook(data: dict) -> dict:
    """Process webhook with idempotency and status priority"""
    
    message_id = data.get("message_id")
    if not message_id:
        raise InvalidCallbackError("Missing message_id")
    
    # Find message by unique ID (idempotency key)
    message = await MessageHistory.find_one(
        MessageHistory.message_id == message_id
    )
    if not message:
        raise DocumentNotFoundError(message_id)
    
    # Get current and new status
    current_status = message.delivery_status
    new_status = map_webhook_status(data.get("status"))
    
    # Only update if status should progress
    if should_update_status(current_status, new_status):
        message.delivery_status = new_status
        message.updated_at = datetime.now(ZoneInfo("Asia/Kolkata"))
        
        # Set timestamp based on status
        if new_status == DeliveryStatus.DELIVERED:
            message.delivered_at = message.updated_at
        elif new_status == DeliveryStatus.READ:
            message.read_at = message.updated_at
        elif new_status == DeliveryStatus.FAILED:
            message.error_message = data.get("error")
        
        await message.save()
        
    return {"status": "processed", "message_id": message_id}
```

### Queue-based Webhook Processing
```python
async def webhook_consumer():
    """Separate consumer for webhook queue - decouples ingestion from processing"""
    
    while True:
        messages = await sqs.receive_messages(
            queue_url=WEBHOOK_QUEUE_URL,
            max_messages=10,
            wait_time=20  # Long polling
        )
        
        for msg in messages:
            try:
                data = json.loads(msg.body)
                await handle_webhook(data)
                await sqs.delete_message(queue_url, msg.receipt_handle)
            except Exception as e:
                logger.error(f"Webhook processing failed: {e}")
                # Message returns to queue after visibility timeout
```

## Key Design Decisions

### Why Status Priority?
Webhooks can arrive out of order due to network delays. A "sent" webhook might arrive after "delivered". Priority system ensures we never lose the more accurate status.

### Why Separate Webhook Queue?
- **Decoupling**: API returns immediately, processing happens async
- **Resilience**: Failed processing retries automatically
- **Scalability**: Scale consumers independently of API
- **Backpressure**: Queue absorbs traffic spikes

### Why Message ID as Idempotency Key?
- Unique per message attempt
- Allows safe retry of failed webhooks
- Prevents duplicate status updates

## Production Considerations
- Set appropriate SQS visibility timeout for processing time
- Implement dead-letter queue for repeated failures
- Add monitoring for queue depth and processing latency
- Log all status transitions for debugging

## GitHub Reference
Pattern implemented in Communication Platform project at Kogta Financial.
