---
doc_id: sla-uptime
doc_type: policy
title: SLA and Uptime Guarantees
---
# SLA and Uptime Guarantees

Our service-level agreement defines the uptime we commit to and the credits you receive if we miss it.

## Uptime commitments

- Growth plan: 99.9% monthly uptime (about 43 minutes of allowable downtime per month)
- Enterprise plan: 99.99% monthly uptime (about 4 minutes of allowable downtime per month)

Starter plans have no SLA. Uptime is measured on the public API and dashboard; scheduled maintenance windows (announced 7 days in advance) are excluded.

## Service credits

If monthly uptime falls below the commitment, you are eligible for credits: 10% of the monthly fee for uptime between 99.0% and 99.9% (Growth), and 25% for uptime below 99.0%. Enterprise tiers double those percentages. Credits are applied to the next invoice — they are not paid out in cash.

## Claiming credits

File a claim within 30 days of the affected month via a support ticket with subject "SLA credit request". Include the dates and times you observed the outage. We verify against our monitoring and respond within 5 business days.

## Status page

Real-time status and 90 days of incident history are published at status.parcelpilot.io. Subscribe to email or webhook notifications for incident updates.
