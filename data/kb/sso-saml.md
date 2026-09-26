---
doc_id: sso-saml
doc_type: guide
title: Setting Up SSO with SAML
---
# Setting Up SSO with SAML

ParcelPilot supports SAML 2.0 single sign-on on Growth and Enterprise plans, so your team can sign in with your identity provider (IdP) such as Okta, Azure AD, or Google Workspace.

## Prerequisites

You need admin access in both ParcelPilot and your IdP, plus your IdP's SAML metadata XML or its metadata URL.

## Configuration steps

1. In ParcelPilot, go to Settings > Security > Single Sign-On and click "Enable SAML".
2. Copy the ACS URL (Assertion Consumer Service URL) and the Entity ID shown on that page into your IdP's application configuration.
3. Upload your IdP metadata XML (or paste the metadata URL) into ParcelPilot.
4. Map the NameID to the user's work email — this must match the email on their ParcelPilot account.
5. Save, then use "Test SSO" before enforcing it.

## Enforcing SSO

After a successful test, toggle "Require SSO for all users" to disable password login. We recommend a 48-hour transition window: enable SSO first, confirm everyone can sign in, then enforce. Keep one break-glass admin account with password login enabled in case your IdP has an outage.

## Troubleshooting

The most common failure is a clock skew between your IdP and our servers — SAML assertions are rejected if timestamps differ by more than 5 minutes. "Invalid signature" errors almost always mean the certificate in ParcelPilot doesn't match the one your IdP is signing with; re-upload the metadata.
