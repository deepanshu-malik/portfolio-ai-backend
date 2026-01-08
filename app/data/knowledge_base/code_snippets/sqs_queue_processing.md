# SQS Queue Processing Pattern

## Overview
Production pattern for processing messages from AWS SQS with concurrent handling, graceful error recovery, and batch operations.

## Problem Solved
Processing high-volume messages requires concurrent handling, graceful errors, and efficient batching without losing messages.

## Consumer Pattern
```python
import asyncio
import json
import boto3

async def sqs_consumer(queue_name: str):
    """Consume and process SQS messages concurrently"""
    sqs = boto3.client("sqs")
    queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
    
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,  # Max batch size
                WaitTimeSeconds=20,      # Long polling
                VisibilityTimeout=300,   # 5 min processing window
            )
            
            messages = response.get("Messages", [])
            if not messages:
                continue
            
            # Process concurrently
            tasks = [process_message(json.loads(m["Body"])) for m in messages]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Delete successful, let failed retry via visibility timeout
            for message, result in zip(messages, results):
                if not isinstance(result, Exception):
                    sqs.delete_message(
                        QueueUrl=queue_url,
                        ReceiptHandle=message["ReceiptHandle"]
                    )
        except Exception as e:
            await asyncio.sleep(5)  # Back off on errors
```

## Batch Sending (FIFO)
```python
async def send_batch_to_sqs(items: list, queue_url: str, batch_id: str):
    """Send messages in batches of 10 with deduplication"""
    sqs = boto3.client("sqs")
    batch_entries = []
    
    for item in items:
        batch_entries.append({
            "Id": str(uuid4()),
            "MessageBody": json.dumps(item, default=str),
            "MessageGroupId": batch_id,
            "MessageDeduplicationId": f"{batch_id}_{item['id']}",
        })
        
        if len(batch_entries) == 10:
            sqs.send_message_batch(QueueUrl=queue_url, Entries=batch_entries)
            batch_entries = []
    
    if batch_entries:  # Send remaining
        sqs.send_message_batch(QueueUrl=queue_url, Entries=batch_entries)
```

## Key Patterns
- **Long Polling**: WaitTimeSeconds=20 reduces API calls
- **Visibility Timeout**: Failed messages auto-retry
- **FIFO Deduplication**: Prevents duplicate processing
- **Batch Operations**: 10 messages per API call
