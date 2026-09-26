---
doc_id: roles-permissions
doc_type: reference
title: Team Roles and Permissions
---
# Team Roles and Permissions

ParcelPilot workspaces have four roles. Permissions are cumulative: each role includes everything below it.

## Roles

- **Viewer**: can view shipments, tracking pages, and reports. Cannot create or modify anything.
- **Operator**: everything a Viewer can do, plus creating shipments, printing labels, and managing tracking numbers.
- **Manager**: everything an Operator can do, plus managing webhooks, API keys, billing settings, and inviting or removing team members.
- **Admin**: full control, including workspace deletion, SSO configuration, audit logs, and role assignment.

Only Admins can change another user's role, and a workspace must always have at least one Admin — the last Admin cannot be demoted or removed.

## Inviting members

Admins and Managers invite members from Settings > Team. Invites expire after 7 days. New members default to the Viewer role; change the role before or after they accept.

## API key scoping

API keys inherit the permissions of the user who created them. A key created by an Operator cannot access billing endpoints. Rotate keys every 90 days; the dashboard flags keys older than 90 days as stale.
