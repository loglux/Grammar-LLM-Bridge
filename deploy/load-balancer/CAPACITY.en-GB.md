# Capacity Analysis and Recommendations

**Date:** 19 December 2025
**Version:** 1.0
**Architecture:** Nginx Load Balancer + 2 Async Backend Instances

---

## Current Architecture

```
                 ┌──────────────┐
                 │   Clients    │
                 │ (Obsidian,   │
                 │  Browser)    │
                 └──────┬───────┘
                        │
                        ↓
               ┌────────────────┐
               │ Nginx Balancer │  ← Port 8081
               │ (round-robin)  │
               └────────┬───────┘
                        │
           ┌────────────┴────────────┐
           ↓                         ↓
 ┌─────────────────┐       ┌─────────────────┐
 │ grammar-llm-01  │       │ grammar-llm-02  │
 │ 4 × workers     │       │ 4 × workers     │
 │ (async uvicorn) │       │ (async uvicorn) │
 └────────┬────────┘       └────────┬────────┘
          │                         │
          └────────────┬────────────┘
                       ↓
              ┌────────────────┐
              │ httpx.AsyncClient │
              │ Pool: 20 conn   │
              └────────┬─────────┘
                       ↓
              ┌────────────────┐
              │  DeepSeek API  │  ← PRIMARY BOTTLENECK
              │  No Rate Limit │
              │  Queue-based   │
              └────────────────┘
```

---

## Configuration

### Backend Containers
- **Instances:** 2 (grammar-llm-01, grammar-llm-02)
- **Workers per instance:** 4 (uvicorn)
- **Total concurrent handlers:** 8

### HTTP Client (httpx.AsyncClient)
- **MAX_CONNECTIONS:** 20 (per process)
- **MAX_KEEPALIVE_CONNECTIONS:** 10
- **LLM_TIMEOUT:** 120s
- **LLM_RETRIES:** 2

### Nginx Load Balancer
- **Port:** 8081
- **Algorithm:** Round-robin
- **Max fails:** 3
- **Fail timeout:** 10s
- **Proxy read timeout:** 130s

---

## Resource Usage

| Container             | CPU   | Memory   | Processes | Status |
|-----------------------|-------|----------|-----------|--------|
| grammar-llm-01        | 0.94% | 171.9 MB | 13        | ✅ Excellent |
| grammar-llm-02        | 1.03% | 168.0 MB | 11        | ✅ Excellent |
| grammar-llm-balancer  | 0.00% | 4.7 MB   | 5         | ✅ Excellent |
| **Total**             | ~1%   | ~345 MB  | 29        | |

**Available:** 31 GB RAM
**Used:** 345 MB (1.1%)
**Scaling headroom:** Massive (10-20× instances possible)

---

## Latency Statistics (from production logs)

**Observation period:** Real user requests

| Metric | Value | Comment |
|--------|-------|---------|
| Minimum | 1.25s | Short texts (100-200 tokens) |
| Median | 3-5s | Normal operation |
| Maximum | 10.14s | With retry (2 LLM calls) |
| Timeouts | 0 | ✅ No signs of overload |

**Conclusion:** DeepSeek API is stable, latency is within normal range.

---

## Throughput Capacity

### Under normal DeepSeek operation (latency 3-5s)

| Text Type | Tokens | Latency | Throughput | Limiting Factor |
|-----------|--------|---------|------------|-----------------|
| Short     | 100-200 | 1-2s | 40-60 req/min | DeepSeek latency |
| Medium    | 500-1000 | 3-5s | 20-30 req/min | **Typical workload** |
| Long      | 2000+ | 5-10s | 10-15 req/min | Possible timeouts |

**Concurrent requests:** 8 (number of workers)
**Queue:** Unlimited (in Nginx → Uvicorn)

### Under DeepSeek overload (latency 30-60s)

⚠️ **CRITICAL:** When DeepSeek servers are under high load:
- Requests hang in queue
- Workers blocked on `await`
- Throughput drops to **5-10 req/min**
- UX degrades (30-120s wait times)

---

## Primary Bottleneck: DeepSeek API

### From official DeepSeek documentation:

> **DeepSeek API does NOT constrain user's rate limit.**
> However, when servers are under high traffic pressure, requests may take time to receive a response. During this period, the connection remains open and you may continuously receive empty lines (non-streaming) or SSE keep-alive comments (streaming).
> If the request has not started inference after 10 minutes, the server will close the connection.

### What this means:

✅ **No hard rate limits** (no 429 errors)
⚠️ **BUT:** Service quality depends on DeepSeek's load
❌ **Risk:** Under overload, latency increases, throughput decreases

### Behaviour during DeepSeek queueing:

1. Client → Nginx → Backend → DeepSeek
2. DeepSeek queued → sends empty lines (keep-alive)
3. httpx keeps connection open (up to 120s timeout)
4. On timeout → retry (up to 2 times)
5. **Total:** up to 6 minutes waiting per request!

---

## Bottlenecks (by priority)

### 1. 🔴 DeepSeek Service Quality (CRITICAL)

**Problem:**
- Unpredictable latency (depends on their load)
- Under overload: workers block → throughput drops
- No control on our side

**Solution:**
- ✅ Implement fallback model (GPT-4o-mini)
- ✅ Monitor latency (alert at >10s)
- ✅ Reduce LLM_TIMEOUT to 60s (faster failover)

### 2. ⚠️ Worker Count (8 total)

**Current state:**
- 2 instances × 4 workers = 8 concurrent handlers
- RAM/CPU usage <1% (can increase)

**BUT:**
- Increasing workers WON'T help with DeepSeek issues
- More workers = more requests → worse DeepSeek quality
- **Recommendation:** Keep as-is until fallback implemented

### 3. 💡 Single Provider (DeepSeek only)

**Risk:**
- DeepSeek issues → entire service degrades
- No backup channel

**Solution:**
- Fallback to GPT-4o-mini (see MULTI_LLM_DESIGN.md)

---

## Scaling Recommendations

### Scenario 1: Personal use (1-2 users)

✅ **Current configuration is optimal**
- 20-30 req/min is sufficient
- Fallback can be deferred
- Monitoring is optional

### Scenario 2: Team (3-10 users)

⚠️ **Fallback implementation MANDATORY**
- Under DeepSeek overload, service becomes unpredictable
- Fallback guarantees stability
- Set up latency monitoring

**Steps:**
1. Implement fallback (MULTI_LLM_DESIGN.md, phase 1)
2. Configure alert for latency >10s
3. Reduce LLM_TIMEOUT to 60s
4. Optional: increase workers to 8 per instance

### Scenario 3: Public service (10+ users)

🔴 **CRITICAL - Full multi-LLM implementation**
- Fallback + language-specific routing
- Add 3rd instance (12 workers total)
- Monitoring: Prometheus + Grafana
- Auto-scaling based on queue depth

**Steps:**
1. Fallback model (phase 1)
2. Language-specific routing (phase 2)
3. Increase instances to 3
4. Workers: 6-8 per instance (18-24 total)
5. Monitor metrics (p50/p95/p99 latency)
6. Rate limiting at Nginx level (DDoS protection)

---

## Practical Action Plan

### Priority 1 - MANDATORY (for production)

- [ ] Implement GPT-4o-mini fallback
  - Trigger: timeout >60s or latency >20s
  - Implementation: see `MULTI_LLM_DESIGN.md`

- [ ] Monitor latency
  - Command: `docker logs grammar-llm-01 | grep "Latency" | grep "llm=[0-9]{4,}"`
  - Alert: latency >10s for 5 minutes

- [ ] Reduce LLM_TIMEOUT to 60s
  - File: `.env.bridge`
  - Reason: Current 120s is too long for UX

### Priority 2 - Recommended

- [ ] Configure smart retry
  - On timeout → fallback instead of DeepSeek retry
  - Time saving: up to 4 minutes per request

- [ ] Increase workers (if throughput needed)
  - Only AFTER fallback implementation
  - Recommendation: 6-8 workers per instance (12-16 total)

- [ ] Metrics logging
  - File: append to app.py
  - Metrics: req/min, latency p50/p95/p99, fallback rate

### Priority 3 - Optional

- [ ] Switch to OpenAI SDK instead of httpx
  - Reason: SDK properly handles DeepSeek keep-alive
  - Risk: Minimal (both libraries work)

- [ ] Test streaming mode
  - May improve UX for long texts
  - Requires client changes (Obsidian plugin)

- [ ] Add third instance
  - Only if throughput >40 req/min consistently
  - Check RAM/CPU before adding

---

## Monitoring

### Status check commands

**Check latency (worst cases):**
```bash
docker logs grammar-llm-01 | grep "Latency(ms):" | \
  awk '{print $2}' | sed 's/llm=//' | sort -n | tail -20
```

**Search for timeouts:**
```bash
docker logs grammar-llm-01 | grep -i "timeout\|429"
```

**Resource usage:**
```bash
docker stats --no-stream grammar-llm-01 grammar-llm-02
```

**Check load balancer:**
```bash
curl http://localhost:8081/health
docker logs grammar-llm-balancer --tail 50
```

### Metrics to track

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| Latency (p50) | <5s | >10s | >30s |
| Latency (p95) | <10s | >20s | >60s |
| Throughput | 20-30/min | <15/min | <5/min |
| Timeout rate | 0% | >5% | >20% |
| Fallback rate | N/A | >30% | >70% |

---

## Known Limitations

1. **DeepSeek API latency is unpredictable**
   - Depends on their traffic
   - Solution: Fallback model

2. **No auto-scaling**
   - Fixed number of instances
   - Solution: Manual scaling when load increases

3. **httpx vs OpenAI SDK**
   - httpx may incorrectly handle many empty lines from DeepSeek
   - Not observed in practice, but risk exists
   - Solution: Monitor JSON parsing errors

4. **Single point of failure**
   - Nginx load balancer in single instance
   - If nginx fails → entire service unavailable
   - Solution: For critical systems - keepalived + 2 nginx

---

## Frequently Asked Questions

**Q: Can we increase workers to 16-32?**
A: Technically yes (RAM allows), but pointless without fallback. Under DeepSeek issues, all workers will block regardless of count, throughput will drop anyway.

**Q: How many users can current configuration handle?**
A: 3-5 active users (Obsidian auto-check every 5s). For more users, implement fallback.

**Q: What to do with persistent timeouts?**
A: 1) Check DeepSeek API status, 2) Temporarily switch everyone to GPT-4o-mini, 3) Implement fallback for automatic switching.

**Q: Should we add a third instance?**
A: Only if monitoring shows consistent load >40 req/min and fallback is already implemented. Otherwise useless.

---

## References

- **Multi-LLM documentation:** `MULTI_LLM_DESIGN.md`
- **Balancer configuration:** `docker-compose.yml`, `lb.conf`
- **DeepSeek API docs:** https://api-docs.deepseek.com/
- **Logs:** `docker logs grammar-llm-01 --tail 100 -f`

---

**Author:** QA Engineer
**Last updated:** 2025-12-19
