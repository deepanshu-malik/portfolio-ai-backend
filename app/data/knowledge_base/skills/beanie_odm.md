# Beanie ODM (MongoDB Async)

## Proficiency: Advanced

## Overview
Beanie is an async MongoDB ODM built on Pydantic and Motor. I use it extensively for building async FastAPI applications with MongoDB.

## Experience
- Built multiple production services with Beanie at Kogta Financial
- Document models with validation, relationships, and custom methods
- Complex aggregation pipelines for reporting
- Embedded documents for denormalized data

## Key Patterns I Use

### Document Models with Validation
```python
from beanie import Document
from pydantic import Field, field_validator

class LeadMaster(Document):
    mobile_no: str = Field(..., alias="MobileNo")
    status: str = Field("pending", alias="Status")
    
    @field_validator("mobile_no", mode="before")
    def validate_mobile(cls, v):
        return v.replace(" ", "").replace("-", "")
    
    class Settings:
        name = "lead_master"  # Collection name
```

### Embedded Documents
```python
class MessageHistory(BaseModel):
    message_id: str
    status: str
    sent_at: datetime

class Lead(Document):
    history: List[MessageHistory] = []  # Embedded array
```

### Aggregation Pipelines
```python
pipeline = [
    {"$match": {"status": "delivered"}},
    {"$group": {
        "_id": "$batch_id",
        "total": {"$sum": 1},
        "success": {"$sum": {"$cond": [{"$eq": ["$status", "delivered"]}, 1, 0]}}
    }}
]
results = await Lead.aggregate(pipeline).to_list()
```

### Async Operations
```python
# Find with filters
leads = await Lead.find(Lead.status == "pending").to_list()

# Update with operators
await Lead.find_one(Lead.id == lead_id).update({"$set": {"status": "sent"}})

# Bulk operations
await Lead.insert_many(leads)
```

## Why Beanie Over PyMongo
- Native async support (works with FastAPI)
- Pydantic validation built-in
- Type hints and IDE support
- Cleaner query syntax
- Document lifecycle hooks

## Projects Using Beanie
- Communication Platform: Message tracking, batch management
- Document Dispatch: Case documents, delivery records
