---
doc_id: tracking-numbers
doc_type: guide
title: Tracking Numbers and Shipment Status
---
# Tracking Numbers and Shipment Status

Every shipment created in ParcelPilot gets a tracking number in the format `PP` followed by 10 digits (e.g., PP1234567890). Customers can follow progress on a branded tracking page.

## Shipment statuses

A shipment moves through: `created` → `label_purchased` → `in_transit` → `out_for_delivery` → `delivered`. Exception states are `failed` (label purchase failed), `returned` (sent back to sender), and `lost` (no carrier scan for 14 days).

## Tracking page

The tracking page URL is `track.parcelpilot.io/<tracking-number>`. You can customize its logo and colors under Settings > Branding. Tracking events appear on the page within 60 seconds of the carrier scan.

## Why a package shows no scans

If a tracking number shows no events after 24 hours, the usual causes are: the label was created but the carrier hasn't picked up the parcel yet, the barcode was damaged and couldn't be scanned, or the tracking number was typed incorrectly. Verify the number format and check with the carrier directly — we display exactly what the carrier reports.

## API lookup

`GET /v1/tracking/{tracking_number}` returns the full event history. Results are cached for 60 seconds, so poll no more than once per minute; subscribe to the `tracking.updated` webhook for real-time changes instead.
