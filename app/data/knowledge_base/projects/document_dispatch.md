# Automated Document Dispatch System

## Overview
Cron-based application dispatching 10,000+ loan welcome letters monthly at Kogta Financial.

## Scale
- 10,000+ documents per month
- Automated generation and dispatch
- Deployed on EKS with CI/CD

## Architecture

### Components
1. Scheduler
   - Cron-based triggers
   - Batch processing logic

2. Document Generator
   - Template engine for letters
   - PDF generation

3. Dispatch Service
   - Integration with Communication Platform
   - Multi-channel delivery (WhatsApp, SMS, Email)

4. Tracking
   - Dispatch status monitoring
   - Retry logic for failures

### Processing Pipeline
1. Cron job triggers batch processor
2. Fetch pending loans from database
3. Generate personalized welcome letters
4. Queue for dispatch via Communication Platform
5. Track delivery status
6. Retry failed dispatches

## Tech Stack
- FastAPI
- SQS (message queue)
- Multiprocessing (parallel generation)
- EKS deployment
- Jenkins/GitLab CI

## Performance Optimization

### Multiprocessing for Generation
Used Python multiprocessing to parallelize document generation. Reduced batch processing time significantly.

### Queue-based Dispatch
Decoupled generation from dispatch using SQS. Prevents bottlenecks and handles failures gracefully.

## My Contributions
- Designed the entire automation workflow
- Implemented multiprocessing for document generation
- Built integration with Communication Platform
- Set up CI/CD pipeline for EKS deployment
