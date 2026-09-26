---
doc_id: webhook-retries
doc_type: guide
title: Webhooks and Retry Behavior
---
# Webhooks and Retry Behavior

ParcelPilot sends webhook events (shipment.created, tracking.updated, label.failed, invoice.paid) to the HTTPS endpoint you configure under Settings > Developers > Webhooks.

## Delivery guarantees

We deliver each event at least once. Your endpoint must respond with HTTP 200 within 10 seconds; anything else — timeouts, 4xx, 5xx — counts as a failed delivery. Use the event's `id` field to deduplicate, since retries can deliver the same event twice.

## Retry schedule

Failed deliveries retry with exponential backoff: after 1 minute, 5 minutes, 30 minutes, 2 hours, and 12 hours — 5 attempts total. After the final failure the event is moved to the dead-letter queue, where it is retained for 7 days and can be replayed manually from the dashboard.

## Securing webhooks

Every request includes an `X-ParcelPilot-Signature` header: an HMAC-SHA256 of the raw request body using your webhook secret. Always verify the signature before processing — reject requests with missing or invalid signatures with HTTP 401. Rotate secrets from the webhook settings page; the old secret stays valid for 24 hours after rotation.

## Testing

Use the "Send test event" button to fire a sample payload at your endpoint, and check the delivery log for status codes and latency per attempt. The log retains 30 days of history.
