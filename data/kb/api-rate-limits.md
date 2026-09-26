---
doc_id: api-rate-limits
doc_type: reference
title: API Rate Limits
---
# API Rate Limits

ParcelPilot enforces rate limits per API key to keep the platform stable. Limits are applied per rolling 60-second window.

## Default limits

- REST API: 1,000 requests per minute per API key
- Tracking webhook events: 5,000 events per minute per account
- Bulk label creation: 200 requests per minute per API key

Enterprise plans can request limit increases through their account manager.

## Handling 429 responses

When you exceed a limit, the API returns HTTP 429 Too Many Requests. Every 429 response includes a `Retry-After` header with the number of seconds to wait before retrying. Do not retry immediately — immediate retries count against the same window and extend the throttle.

## Best practices

Implement exponential backoff: wait 1 second, then 2, then 4, up to a maximum of 60 seconds between retries. Cache tracking-number lookups instead of polling — use webhooks to receive status changes in real time. Batch label requests with the bulk endpoint rather than looping single calls.

## Monitoring usage

Response headers `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` show your quota, remaining calls, and the Unix timestamp when the window resets. The dashboard under Developers > Usage graphs per-key consumption for the last 30 days.
