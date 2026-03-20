# Cookie Policy

**Effective Date:** March 28, 2026
**Last Updated:** 2026-03-20

---

## 1. Introduction

This Cookie Policy explains how **BangDesign Co. Ltd.** ("Company", "we", "us", or "our") uses cookies, local storage, and similar technologies on **Evidoc** ("Service") at [https://evidoc.hulkdesign.com](https://evidoc.hulkdesign.com).

This policy should be read alongside our [Privacy Policy](./PRIVACY_POLICY.md) and [Terms of Service](./TERMS_OF_SERVICE.md).

---

## 2. What Are Cookies and Local Storage?

- **Cookies** are small text files stored on your device by your web browser. They can be "session" cookies (deleted when you close your browser) or "persistent" cookies (remaining until they expire or you delete them).
- **Local Storage** and **Session Storage** are browser-based storage mechanisms that allow websites to store data on your device. Session storage is cleared when the browser tab is closed; local storage persists until explicitly cleared.

---

## 3. Technologies We Use

### 3.1 Strictly Necessary (No Consent Required)

These are essential for the Service to function. Disabling them will prevent you from using Evidoc.

| Technology | Type | Purpose | Duration |
|------------|------|---------|----------|
| **MSAL authentication state** | Session Storage | Stores authentication tokens (Azure AD / B2C login session). Required for secure access to your account. | Browser session |
| **MSAL auth state cookie** | Cookie | Fallback authentication state for browser compatibility (IE11/Edge). Only set when `storeAuthStateInCookie` is enabled. | Browser session |
| **selectedFolderId** | Session Storage | Remembers which document folder you are viewing during your session. | Browser session |

### 3.2 Functional (No Consent Required)

These remember your preferences to improve your experience but are not essential.

| Technology | Type | Purpose | Duration |
|------------|------|---------|----------|
| **showOriginalText** | Local Storage | Remembers your preference for displaying original text alongside translations. | Persistent (until cleared) |
| **UI preferences** | Local Storage | Stores layout and display preferences (e.g., sidebar state). | Persistent (until cleared) |

### 3.3 Analytics (Opt-In — Consent Required)

These are only activated when analytics is explicitly enabled. They help us understand how the Service is used so we can improve it. **No document content or query text is collected.**

| Technology | Type | Purpose | Duration | Provider |
|------------|------|---------|----------|----------|
| **PostHog session data** | Local Storage | Stores a pseudonymized user identifier and session state for product analytics. Tracks events such as query sent, file uploaded, citation clicked, and dashboard viewed. | Persistent (until cleared) | PostHog |
| **PostHog cookies** | Cookie | PostHog may set cookies for session tracking depending on configuration. | Varies | PostHog |

**PostHog configuration details:**
- `autocapture: false` — We only track explicitly defined events, not all clicks/interactions
- `capture_pageview: true` — Page views are tracked
- `capture_pageleave: true` — Page exits are tracked
- `persistence: "localStorage"` — PostHog uses local storage (not cookies) by default

### 3.4 Error Tracking (Opt-In)

| Technology | Type | Purpose | Duration | Provider |
|------------|------|---------|----------|----------|
| **Sentry session** | Local Storage / Cookie | Stores a session identifier for error tracking. Captures error stack traces and metadata. **PII is stripped before transmission** (console breadcrumb messages are removed). | Browser session | Sentry |

**Sentry configuration details:**
- Transaction sample rate: 10%
- Error replay sample rate: 50%
- No query text, document content, or personal messages are sent to Sentry

---

## 4. What We Do NOT Use

- ❌ **Third-party advertising cookies** — We do not serve ads or use ad tracking
- ❌ **Cross-site tracking cookies** — We do not track you across other websites
- ❌ **Social media tracking pixels** — We do not embed Facebook Pixel, Google Analytics, or similar trackers
- ❌ **Fingerprinting** — We do not use browser fingerprinting techniques

---

## 5. Managing Your Preferences

### 5.1 Browser Controls

You can manage cookies and local storage through your browser settings:

- **Chrome:** Settings → Privacy and Security → Cookies and other site data
- **Firefox:** Settings → Privacy & Security → Cookies and Site Data
- **Safari:** Preferences → Privacy → Manage Website Data
- **Edge:** Settings → Cookies and site permissions

### 5.2 Clearing Local Storage

To clear local storage for Evidoc:
1. Open your browser's Developer Tools (F12)
2. Navigate to the "Application" or "Storage" tab
3. Select "Local Storage" → select the Evidoc domain
4. Click "Clear All" or remove specific entries

### 5.3 Opt-Out of Analytics

Analytics (PostHog) is only active when the `VITE_POSTHOG_KEY` environment variable is configured. If you wish to opt out:
- Contact us at support@hulkdesign.com to request analytics opt-out
- Use a browser extension that blocks PostHog (e.g., uBlock Origin)
- Clear PostHog data from local storage

### 5.4 Impact of Disabling Technologies

| If You Disable... | Impact |
|--------------------|--------|
| Session Storage | You will be unable to log in or maintain a session |
| Local Storage (all) | UI preferences will reset on each visit; analytics will not persist |
| Analytics cookies/storage only | No impact on Service functionality |
| All cookies | Authentication may not work in some browsers |

---

## 6. Cookie Consent

In accordance with the PDPA and GDPR (for EU/EEA users):

- **Strictly necessary technologies** do not require consent and are active by default
- **Analytics technologies** require your explicit consent before activation
- You may withdraw your consent at any time without affecting the functionality of the Service (only analytics will be disabled)

When you first visit the Service, you will be presented with a cookie consent banner that allows you to:
- **Accept all** — enables all technologies including analytics
- **Necessary only** — enables only strictly necessary technologies
- **Customize** — choose which categories to enable

Your consent preference is stored locally and can be changed at any time through the Service's settings.

---

## 7. Data Transfers

Analytics data processed by PostHog and Sentry may be transferred internationally. See our [Privacy Policy](./PRIVACY_POLICY.md) Section 7 for details on international data transfer safeguards.

---

## 8. Changes to This Cookie Policy

We may update this Cookie Policy when we add or remove technologies. Material changes will be communicated via:
- Updated "Last Updated" date at the top of this page
- A refreshed cookie consent prompt if new categories are introduced

---

## 9. Contact Us

For questions about this Cookie Policy:

**BangDesign Co. Ltd.**
Email: support@hulkdesign.com
Subject: "Cookie Policy Inquiry"

---

*This Cookie Policy was last updated on 2026-03-20.*
