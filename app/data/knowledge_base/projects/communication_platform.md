# Multi-Channel Communication Platform

## Overview
Enterprise-grade messaging platform handling WhatsApp, SMS, and RCS communications for a fintech organization. Built from scratch to serve internal teams and customer-facing notifications at scale.

## Scale & Impact
- Processes thousands of messages daily across multiple channels
- Handles 10,000+ automated document dispatches monthly
- Real-time webhook processing for delivery status tracking
- Supports batch campaigns with Excel-based bulk uploads
- Multi-tenant architecture serving different business units

## Architecture

### System Design
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│  Message    │────▶│  Consumer   │
│   (API)     │     │   Queue     │     │  (Worker)   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       ▼                                       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   MongoDB   │     │    SQL      │     │  Channel    │
│  (Primary)  │     │ Databases   │     │  Providers  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       ▼                                       ▼
┌─────────────┐                         ┌─────────────┐
│   Search    │                         │  Webhooks   │
│   Engine    │                         │  (Status)   │
└─────────────┘                         └─────────────┘
```

### Message Flow
1. API receives batch request
2. Batch record created with PENDING status
3. Lead/recipient records created for each message
4. Messages queued for async processing
5. Consumer workers process messages in parallel
6. Channel-specific sender dispatches message
7. Webhook receives delivery status callback
8. Status updated with complete audit trail
9. Batch completion auto-detected when all leads processed

### Components
- **API Layer**: FastAPI with versioned REST endpoints
- **Queue Layer**: AWS SQS for message and webhook processing
- **Consumer Workers**: Separate processes for sending and webhook handling
- **Storage Layer**: MongoDB (Beanie ODM) + SQL databases for business data
- **Search Layer**: OpenSearch for analytics and reporting

## Tech Stack

### Core
- **Framework**: FastAPI (async Python)
- **Primary Database**: MongoDB with Beanie ODM
- **Message Queue**: AWS SQS
- **File Storage**: AWS S3
- **Search**: OpenSearch

### Multi-Database Integration
- **MongoDB**: Primary data store (batches, leads, templates, message history)
- **MySQL**: Business system integration
- **MSSQL**: Legacy system integration
- **Redshift**: Analytics and reporting

### Messaging Channels
| Channel | Features |
|---------|----------|
| WhatsApp | Template-based messaging, sync/async modes, interactive buttons |
| SMS | Delivery callbacks, regulatory compliance |
| RCS | Rich Communication Services support |

### Infrastructure
- **Deployment**: Kubernetes (EKS)
- **CI/CD**: Jenkins + GitLab CI
- **Auth**: JWT-based authentication
- **Secrets**: AWS Secrets Manager
- **Containerization**: Docker

## Key Features

### Batch Processing
- Excel-based bulk message campaigns
- Validation before processing
- Split batch by status (resend failed only)
- Cancel batch functionality
- Real-time progress tracking

### Plugin Architecture for Business Units
Extensible architecture with pluggable business logic:
- Abstract base class defining standard interface
- Decorator-based registration system
- Each business unit implements custom logic
- Automatic discovery at startup

Each plugin implements:
- Campaign listing with filters
- Message processing with template parameters
- Channel-specific sending logic
- Aggregated statistics
- Excel export functionality

### Webhook Handling
- Real-time delivery status updates
- Idempotent webhook processing
- Status priority management (prevents status downgrades)
- Customer response tracking (button callbacks)
- External system callback integration

### Message History & Audit Trail
- Complete audit trail per recipient
- Embedded message history documents
- Status tracking: PENDING → SENT → DELIVERED → READ
- Error capture for failures
- Timestamp tracking (sent_at, delivered_at, read_at)

## Database Design

### Batch Record
- Batch identifier and metadata
- Template reference
- Status tracking (PENDING, PROCESSING, COMPLETED, CANCELLED, FAILED)
- Progress counters (total, processed, success, failed)

### Lead/Recipient Record
- Batch reference
- Recipient details
- Message and delivery status
- Template parameters
- Embedded message history array

### Message History (Embedded)
- Unique message identifier
- Channel type
- Status with timestamps
- Error details if failed

## Design Patterns Used

### Adapter Pattern
Channel-specific message senders implement common interface. Easy addition of new channels without modifying core logic.

### Repository Pattern
Centralized data access for templates and sender configurations.

### Plugin Architecture
Business unit logic isolated in pluggable modules with standard interface.

### Queue-based Processing
Decoupled async operations for scalability and fault tolerance.

### Idempotent Webhooks
Message ID-based deduplication prevents duplicate processing.

## Challenges & Solutions

### Challenge: High-volume webhook processing
**Solution**: Dedicated webhook queue with separate consumer process. Decouples ingestion from processing, prevents timeouts during traffic spikes.

### Challenge: Multi-provider abstraction
**Solution**: Adapter pattern for messaging channels. Common `send_message()` interface, provider-specific implementations. New channels added without core changes.

### Challenge: Delivery tracking accuracy
**Solution**: Idempotent handlers with message ID deduplication. Status priority system prevents downgrades (DELIVERED won't revert to SENT).

### Challenge: Multi-database integration
**Solution**: Database manager utility for SQL connections. Each business unit queries its data source. MongoDB remains primary with async Beanie ODM.

### Challenge: Business unit extensibility
**Solution**: Plugin architecture with abstract base class and decorator registration. New units implement standard interface, auto-registered at startup.

## Testing
- Comprehensive test suite with 170+ tests
- Unit tests for services, models, utilities
- API endpoint tests
- Integration tests for workflows
- Coverage reporting

## My Contributions
- Designed and implemented entire platform architecture from scratch
- Built all FastAPI microservices and REST endpoints
- Integrated multiple messaging channel providers
- Designed multi-database integration layer
- Implemented plugin system for business units
- Built SQS-based async processing pipeline
- Created webhook handling with idempotent processing
- Wrote comprehensive test suite
- Deployed on Kubernetes with CI/CD pipeline

## Skills Demonstrated
- **System Design**: Scalable multi-channel messaging architecture
- **Async Programming**: Full async implementation with FastAPI/Beanie
- **Queue-based Architecture**: SQS for decoupled processing
- **Multi-database Integration**: MongoDB, MySQL, MSSQL, Redshift
- **Plugin Architecture**: Extensible business logic modules
- **Webhook Processing**: Idempotent status handling
- **Testing**: Comprehensive test coverage
- **DevOps**: Kubernetes deployment, CI/CD pipelines
