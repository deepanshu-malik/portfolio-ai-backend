# Koyeb Free Tier Optimization Plan

## Overview
This document outlines the implementation plan for optimizing the Portfolio AI Backend for deployment on Koyeb's free tier (512MB RAM, ephemeral storage, single instance).

## Implementation Timeline

### Phase 1: Critical Infrastructure (Points 1-6)
**Goal:** Ensure app runs reliably on Koyeb free tier

#### 1. Cold Start Optimization ✓
**Files to modify:**
- `app/main.py` - Add startup event with service warming
- `app/routers/health.py` - Add lightweight `/ping` endpoint

**Changes:**
- Pre-load ChromaDB and services on startup
- Add ping endpoint for external keep-alive services
- Log startup timing for monitoring

**Testing:**
- Verify cold start time < 10 seconds
- Test with cron-job.org keep-alive

---

#### 2. ChromaDB Persistence Fix ✓
**Files to modify:**
- `Dockerfile` - Ensure data baked into image
- `app/main.py` - Add ChromaDB verification on startup
- `scripts/ingest.py` - Add verification logic

**Changes:**
- Copy knowledge base at build time
- Run ingestion during Docker build
- Verify data on startup, re-ingest if empty
- Log document count on startup

**Testing:**
- Build Docker image and verify ChromaDB populated
- Deploy to Koyeb and check logs for document count

---

#### 3. Memory Optimization ✓
**Files to modify:**
- `app/config.py` - Add memory-related settings
- `app/middleware/timeout.py` - Create new timeout middleware
- `app/main.py` - Add timeout middleware
- `app/services/session_manager.py` - Update max history length

**Changes:**
- Add `max_concurrent_requests`, `request_timeout`, `max_history_length`
- Create timeout middleware (30s timeout)
- Reduce session history from 10 to 5 messages
- Add memory usage monitoring

**Testing:**
- Verify requests timeout after 30s
- Monitor memory usage under load
- Test with concurrent requests

---

#### 4. Graceful Degradation ✓
**Files to modify:**
- `app/services/advanced_response_generator.py` - Add retry logic
- `app/routers/chat_v2.py` - Add fallback handling
- `requirements.txt` - Add tenacity library

**Changes:**
- Add exponential backoff with tenacity (2 retries)
- Add fallback response for OpenAI failures
- Log all failures with context
- Return user-friendly error messages

**Testing:**
- Simulate OpenAI API failures
- Verify fallback responses work
- Check retry logic with delays

---

#### 5. Koyeb-Specific Configuration ✓
**Files to create:**
- `koyeb.yaml` - Koyeb deployment configuration

**Changes:**
- Define service with nano instance type
- Set health check configuration
- Define environment variables
- Configure scaling (min=1, max=1)
- Set region (Frankfurt for EU, or closest)

**Testing:**
- Validate YAML syntax
- Deploy to Koyeb and verify configuration applied

---

#### 6. Enhanced Health Checks ✓
**Files to modify:**
- `app/routers/health.py` - Enhance health check endpoint
- `requirements.txt` - Add psutil for memory monitoring

**Changes:**
- Add ChromaDB status check (document count)
- Add OpenAI key validation check
- Add memory usage reporting
- Return detailed status (healthy/degraded/unhealthy)
- Add timestamp to all responses

**Testing:**
- Call `/api/health` and verify all checks pass
- Simulate ChromaDB failure and check degraded status
- Monitor memory reporting

---

### Phase 2: Cost Optimization (Points 7-9)
**Goal:** Minimize OpenAI API costs

#### 7. Simple Response Caching ✓
**Files to create:**
- `app/services/cache.py` - In-memory cache with TTL

**Files to modify:**
- `app/routers/chat_v2.py` - Integrate caching
- `app/config.py` - Add cache TTL setting

**Changes:**
- Create SimpleCache class with 30-minute TTL
- Cache responses by message+intent hash
- Limit cache to 100 most recent entries
- Add cache hit/miss logging
- Add cache statistics endpoint

**Testing:**
- Send duplicate messages and verify cached response
- Verify TTL expiration after 30 minutes
- Check memory usage with full cache

---

#### 8. Reduce Token Usage ✓
**Files to modify:**
- `app/config.py` - Update token limits
- `app/services/advanced_response_generator.py` - Use new limits
- `app/services/hybrid_retriever.py` - Reduce retrieval count

**Changes:**
- Reduce `max_tokens_context`: 3000 → 2000
- Reduce `max_tokens_history`: 1000 → 500
- Reduce `max_tokens_response`: 800 → 600
- Reduce `max_retrieval_docs`: 5 → 3

**Testing:**
- Verify responses still coherent with lower limits
- Monitor token usage reduction
- Check cost savings in stats endpoint

---

#### 9. Batch Similar Requests (Request Deduplication) ✓
**Files to create:**
- `app/services/deduplication.py` - Request deduplication service

**Files to modify:**
- `app/routers/chat_v2.py` - Add deduplication layer

**Changes:**
- Create request deduplication with asyncio
- Hash messages and deduplicate concurrent requests
- Share responses across duplicate requests
- Add metrics for deduplication rate

**Testing:**
- Send 10 identical concurrent requests
- Verify only 1 OpenAI call made
- Check all requests receive same response

---

### Phase 3: Operational Excellence (Points 10-12)
**Goal:** Improve reliability and debuggability

#### 10. Startup/Readiness Probes ✓
**Files to modify:**
- `app/main.py` - Add readiness state management
- `app/routers/health.py` - Add `/ready` endpoint

**Changes:**
- Add global `ready` flag
- Set ready=True after successful startup
- Create `/ready` endpoint (returns 503 if not ready)
- Koyeb uses `/ready` for traffic routing

**Testing:**
- Start app and verify `/ready` returns 503 initially
- Verify `/ready` returns 200 after startup complete
- Simulate startup failure and check 503 persists

---

#### 11. Environment Validation ✓
**Files to modify:**
- `app/main.py` - Add validation on startup
- `app/config.py` - Add validation methods

**Changes:**
- Validate OPENAI_API_KEY is set
- Validate rate limit settings are reasonable
- Check ChromaDB directory exists
- Fail fast with clear error messages
- Log all configuration on startup

**Testing:**
- Start without OPENAI_API_KEY and verify failure
- Set invalid rate limits and verify correction
- Check logs show all configuration

---

#### 12. Better Logging for Debugging ✓
**Files to modify:**
- `app/main.py` - Add structured logging and request middleware

**Changes:**
- Configure structured logging to stdout
- Add request/response logging middleware
- Log: method, path, status, duration, client IP
- Add correlation IDs for request tracing
- Log all errors with full context

**Testing:**
- Make requests and verify all logged
- Check log format is parseable
- Verify error logs include stack traces
- Monitor Koyeb logs for proper output

---

## File Changes Summary

### New Files (6)
1. `KOYEB_OPTIMIZATION_PLAN.md` - This document
2. `koyeb.yaml` - Koyeb deployment config
3. `app/middleware/timeout.py` - Request timeout middleware
4. `app/services/cache.py` - Response caching service
5. `app/services/deduplication.py` - Request deduplication service
6. `.env.koyeb.example` - Example environment variables for Koyeb

### Modified Files (9)
1. `app/main.py` - Startup, readiness, validation, logging
2. `app/config.py` - Memory limits, cache settings, token limits
3. `app/routers/health.py` - Enhanced health checks, ping endpoint
4. `app/routers/chat_v2.py` - Caching, deduplication, fallback
5. `app/services/advanced_response_generator.py` - Retry logic, token limits
6. `app/services/session_manager.py` - Reduced history length
7. `app/services/hybrid_retriever.py` - Reduced document count
8. `Dockerfile` - ChromaDB persistence improvements
9. `requirements.txt` - Add tenacity, psutil

### Updated Files (1)
1. `README.md` - Add Koyeb deployment instructions

---

## Testing Strategy

### Local Testing
1. Build Docker image: `docker build -t portfolio-ai .`
2. Run container: `docker run -p 8000:8000 --env-file .env portfolio-ai`
3. Test all endpoints: health, ready, ping, chat
4. Monitor logs for errors
5. Check memory usage: `docker stats`

### Koyeb Testing
1. Deploy to Koyeb
2. Monitor startup logs
3. Test cold start performance
4. Verify health checks passing
5. Monitor memory usage in dashboard
6. Test with real traffic
7. Set up keep-alive with cron-job.org

### Load Testing (Optional)
1. Use `wrk` or `ab` for basic load testing
2. Send 100 requests over 1 minute
3. Monitor response times and memory
4. Verify no OOM errors
5. Check cache hit rates

---

## Expected Outcomes

### Performance Metrics
- **Cold start time:** < 10 seconds (down from ~20s)
- **Warm response time:** 1-3 seconds (cached)
- **Uncached response time:** 3-5 seconds
- **Memory usage:** 300-400MB (within 512MB limit)
- **Cache hit rate:** 30-40% (varies by traffic)

### Cost Savings
- **Token reduction:** ~40% (from reduced context/history)
- **Cache savings:** ~30% fewer OpenAI calls
- **Total savings:** ~55-60% on OpenAI costs

### Reliability Improvements
- **Uptime:** 99%+ (with keep-alive)
- **Error rate:** < 1% (with graceful degradation)
- **Timeout rate:** < 0.5% (with proper limits)

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing locally
- [ ] Docker build succeeds
- [ ] ChromaDB populated in image
- [ ] Environment variables documented
- [ ] README updated with Koyeb instructions

### Koyeb Setup
- [ ] Create Koyeb account
- [ ] Connect GitHub repository
- [ ] Set OPENAI_API_KEY secret
- [ ] Configure health check path: `/api/health`
- [ ] Select nano instance (free tier)
- [ ] Enable auto-deploy from main branch
- [ ] Configure custom domain (optional)

### Post-Deployment
- [ ] Verify app is running
- [ ] Check health endpoint returns 200
- [ ] Test chat endpoint
- [ ] Monitor logs for errors
- [ ] Set up keep-alive ping (cron-job.org)
- [ ] Monitor token usage
- [ ] Check cache hit rates

### Monitoring (First 24 Hours)
- [ ] Check uptime percentage
- [ ] Monitor memory usage trends
- [ ] Review error logs
- [ ] Analyze response times
- [ ] Verify cache effectiveness
- [ ] Check OpenAI costs

---

## Rollback Plan

If issues occur after deployment:

1. **High Memory Usage (>450MB):**
   - Reduce `max_concurrent_requests` to 2
   - Reduce cache size to 50 entries
   - Reduce `max_history_length` to 3

2. **Slow Response Times:**
   - Verify keep-alive is working
   - Check OpenAI API status
   - Review timeout settings
   - Increase timeout to 45s if needed

3. **Frequent Crashes:**
   - Check logs for OOM errors
   - Verify ChromaDB loaded correctly
   - Review startup validation errors
   - Consider disabling cache temporarily

4. **OpenAI Rate Limits:**
   - Increase retry delays
   - Reduce max concurrent requests
   - Add longer cache TTL (1 hour)

---

## Future Enhancements (Post-Koyeb)

Once stable on Koyeb free tier:

1. **Upgrade to paid tier** if traffic increases
2. **Add Redis** for distributed caching (if multi-instance)
3. **Add PostgreSQL** for persistent conversation storage
4. **Add Sentry** for error tracking
5. **Add Analytics** dashboard for usage insights
6. **Add A/B testing** for prompt optimization
7. **Add WebSocket** for real-time features (if memory allows)

---

## Notes

- All changes maintain backwards compatibility
- No breaking API changes
- All new features have feature flags where appropriate
- Documentation updated inline with code changes
- Logging follows structured format for parsing

---

## Success Criteria

This optimization plan is considered successful when:

1. ✅ App deploys successfully to Koyeb free tier
2. ✅ Cold start time < 10 seconds
3. ✅ Memory usage stays under 450MB (90% of limit)
4. ✅ No crashes or OOM errors for 24 hours
5. ✅ Health checks passing consistently
6. ✅ Response times < 5 seconds (95th percentile)
7. ✅ Cache hit rate > 30%
8. ✅ Token costs reduced by > 50%
9. ✅ Error rate < 1%
10. ✅ Uptime > 99% (with keep-alive)

---

**Plan Created:** 2026-01-10
**Status:** Ready for Implementation
**Estimated Implementation Time:** 3-4 hours
**Priority:** High (Required for Koyeb deployment)
