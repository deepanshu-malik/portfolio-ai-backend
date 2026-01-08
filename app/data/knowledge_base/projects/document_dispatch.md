# Automated Document Dispatch System

## Overview
Cron-based automation system that generates and dispatches personalized loan welcome letters at scale. Handles the complete lifecycle from data extraction, PDF generation, multi-channel delivery (WhatsApp, RCS, Courier), to delivery tracking and retry management.

## Scale & Impact
- Processes 10,000+ documents monthly
- Automated end-to-end workflow replacing manual processes
- Multi-language support (English, Hindi, Marathi, Gujarati)
- Multi-channel delivery with automatic fallback
- Failed delivery retry mechanism
- Complete audit trail and delivery tracking

## Architecture

### System Components
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Scheduler     │────▶│   SQS Queue     │────▶│   Consumer      │
│   (Cronjob)     │     │   (FIFO)        │     │   (Worker)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        ▼                                               ▼
┌─────────────────┐                           ┌─────────────────┐
│   Redshift      │                           │  PDF Generator  │
│   (Data Source) │                           │  (WeasyPrint)   │
└─────────────────┘                           └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   MongoDB       │◀────│   S3 Storage    │◀────│  Notification   │
│   (Tracking)    │     │   (PDFs)        │     │  (WA/RCS/SMS)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Processing Pipeline
1. **Scheduler (Cronjob)**: Runs daily, queries data warehouse for new disbursements
2. **Data Extraction**: Fetches loan details and EMI schedules from Redshift
3. **Queue Distribution**: Pushes individual cases to SQS FIFO queue
4. **Consumer Processing**: Workers process messages concurrently
5. **PDF Generation**: Creates multi-page welcome letter with EMI schedule
6. **S3 Upload**: Stores generated PDFs with parallel uploads
7. **Notification**: Sends via WhatsApp with RCS fallback
8. **Status Tracking**: Records delivery status in MongoDB
9. **Retry Handling**: Failed cases automatically retried in subsequent runs

## Tech Stack

### Core
- **Framework**: FastAPI (async Python)
- **Database**: MongoDB (Beanie ODM)
- **Queue**: AWS SQS (FIFO)
- **Storage**: AWS S3
- **PDF Generation**: WeasyPrint + Jinja2 templates

### Data Sources
- **Redshift**: Data warehouse for loan application data
- **MySQL**: Loan origination system updates
- **OpenSearch**: Search index updates

### Infrastructure
- **Deployment**: Kubernetes (EKS)
- **CI/CD**: Jenkins + GitLab CI
- **Secrets**: AWS Secrets Manager
- **Monitoring**: Email alerts for failures

## Key Features

### PDF Generation
- **Multi-language Support**: English, Hindi, Marathi, Gujarati templates
- **Dynamic Content**: Personalized with loan details, EMI schedules
- **Multi-page Documents**: Welcome letter + EMI schedule + Terms
- **Parallel Generation**: Concurrent PDF creation using asyncio
- **Template Engine**: Jinja2 HTML templates rendered to PDF

### Parallel Processing
```python
# Generate PDFs concurrently
tasks = [
    loop.run_in_executor(None, self._generate_pdf, "WelcomeLetterEnglish.html"),
    loop.run_in_executor(None, self._generate_pdf, "EmiSchedule.html"),
    loop.run_in_executor(None, self._generate_pdf, "ScheduleOfCharges.html"),
]
pdf_results = await asyncio.gather(*tasks)
```

### Multi-Channel Delivery
- **Primary**: WhatsApp Business API
- **Fallback**: RCS (Rich Communication Services)
- **Physical**: Courier dispatch with tracking
- **Automatic Fallback**: If WhatsApp fails, automatically tries RCS

### Batch Processing
- **Chunked Data Fetching**: Processes large datasets in chunks of 32
- **SQS Batch Sending**: Groups messages in batches of 10 for efficiency
- **Deduplication**: Message deduplication IDs prevent duplicate processing
- **FIFO Ordering**: Maintains processing order within batches

### Retry Mechanism
- **Automatic Retry**: Failed cases queried and reprocessed
- **Configurable Window**: Retry cases from last N days
- **Pending Case Detection**: Identifies failed deliveries in MongoDB
- **Reuses Existing PDFs**: Pending retries skip PDF regeneration

### Delivery Tracking
- **Complete Audit Trail**: Every delivery attempt recorded
- **Status History**: Sent → Delivered/Failed with timestamps
- **Multiple Channels**: Tracks WhatsApp, RCS, and Courier separately
- **Batch Statistics**: Aggregated success/failure counts per batch

## Database Models

### CaseDocumentData
Primary document tracking all case information:
- Loan application identifiers
- Applicant details (name, address, contact)
- Financial details (loan amount, EMI, IRR)
- S3 file references
- Delivery status and timestamps
- Batch information

### CaseDocumentDeliveryData
Delivery attempt history:
- Message mode (WhatsApp/RCS/Courier)
- Status (Sent/Delivered/Failed)
- Failure reasons
- Timestamps
- Courier tracking details

## Processing Modes

### New Case Processing
1. Fetch loan data from Redshift
2. Generate personalized PDFs
3. Upload to S3
4. Send notification
5. Create MongoDB records

### Pending Case Retry
1. Query MongoDB for failed cases
2. Reuse existing S3 PDFs
3. Retry notification
4. Update delivery records

### Courier Dispatch
1. Upload Excel with tracking details
2. Validate all cases in batch
3. Update status to Delivered
4. Create courier delivery records

## Error Handling

### Alert System
- Email notifications for critical failures
- Scheduler errors with batch context
- Consumer errors with case details
- Database operation failures

### Graceful Degradation
- Continue processing if individual cases fail
- Log errors without stopping batch
- Retry failed messages via SQS visibility timeout

## Configuration

### Scheduler Options
- Manual date range override
- Configurable days back for auto-scheduling
- Pending cases processing toggle
- Timezone configuration

### Environment Variables
- Database connections (MongoDB, MySQL, Redshift)
- AWS services (SQS, S3, Secrets Manager)
- Notification service endpoints
- Alert email recipients

## Deployment

### Multiple Containers
1. **API Service**: FastAPI for manual operations and status queries
2. **Consumer**: SQS message processor for document generation
3. **Scheduler Cronjob**: Daily batch trigger
4. **Alert Cronjob**: Failed delivery notifications

### Kubernetes Resources
- Deployments for API and Consumer
- CronJobs for scheduled tasks
- ConfigMaps for environment configuration
- Secrets for credentials

## My Contributions
- Designed complete automation architecture from scratch
- Implemented parallel PDF generation with WeasyPrint
- Built SQS-based distributed processing pipeline
- Created multi-channel notification system with fallback
- Developed retry mechanism for failed deliveries
- Implemented courier tracking with Excel upload
- Built comprehensive alert system for monitoring
- Deployed on Kubernetes with CI/CD pipeline

## Skills Demonstrated
- **Async Programming**: asyncio, aiohttp, aiomysql for concurrent operations
- **PDF Generation**: WeasyPrint, Jinja2 templates, PDF merging
- **Queue Architecture**: SQS FIFO with batching and deduplication
- **Multi-database**: MongoDB, MySQL, Redshift integration
- **Data Processing**: Pandas for Excel handling, chunked data fetching
- **Error Handling**: Comprehensive alerting and graceful degradation
- **DevOps**: Kubernetes CronJobs, multi-container deployment
