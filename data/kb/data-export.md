---
doc_id: data-export
doc_type: howto
title: Exporting Your Data
---
# Exporting Your Data

You can export shipments, tracking events, invoices, and user activity from ParcelPilot at any time. Exports are available in CSV and JSON formats.

## On-demand exports

Go to Reports > Export, choose a data type and date range (maximum 12 months per export), pick CSV or JSON, and click "Generate". Small exports download immediately; larger ones are prepared in the background and you'll receive an email with a download link.

## Export retention

Generated export files are kept for 14 days, then deleted automatically. Download links expire with the file. Re-running an export for the same range creates a new file.

## Scheduled exports

Enterprise plans can schedule recurring exports (daily, weekly, or monthly) to an S3 bucket or SFTP server you control. Configure the destination under Settings > Integrations > Scheduled Exports. Files are delivered as gzip-compressed CSV.

## Limits and notes

Each export is capped at 2 million rows; split larger ranges into multiple exports. Deleted shipments are excluded from exports. Timestamps are in UTC using ISO 8601 format. Personally identifiable information is included unless your workspace has PII redaction enabled under Settings > Privacy.
