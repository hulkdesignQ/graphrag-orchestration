/**
 * Analytics service — PostHog product analytics + Sentry error tracking.
 *
 * Opt-in: Only activates when the corresponding env var is set.
 *   - VITE_POSTHOG_KEY: PostHog project API key
 *   - VITE_POSTHOG_HOST: PostHog instance URL (default: https://us.i.posthog.com)
 *   - VITE_SENTRY_DSN: Sentry DSN for error tracking
 *
 * Usage:
 *   import { analytics } from "../analytics";
 *   analytics.track("query_sent", { language: "en" });
 */

import posthog from "posthog-js";
import * as Sentry from "@sentry/react";

// ── PostHog ─────────────────────────────────────────────────────────────

const POSTHOG_KEY = import.meta.env.VITE_POSTHOG_KEY as string | undefined;
const POSTHOG_HOST = (import.meta.env.VITE_POSTHOG_HOST as string) || "https://us.i.posthog.com";

let posthogReady = false;

export function initAnalytics(): void {
    // PostHog
    if (POSTHOG_KEY) {
        posthog.init(POSTHOG_KEY, {
            api_host: POSTHOG_HOST,
            autocapture: false, // explicit events only — keeps data clean
            capture_pageview: true,
            capture_pageleave: true,
            persistence: "localStorage",
        });
        posthogReady = true;
    }

    // Sentry
    const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN as string | undefined;
    if (SENTRY_DSN) {
        Sentry.init({
            dsn: SENTRY_DSN,
            environment: import.meta.env.MODE || "production",
            tracesSampleRate: 0.1, // 10% of transactions
            replaysSessionSampleRate: 0,
            replaysOnErrorSampleRate: 0.5,
            beforeSend(event) {
                // Strip PII from breadcrumbs (don't send query text)
                if (event.breadcrumbs) {
                    event.breadcrumbs = event.breadcrumbs.map(b => {
                        if (b.category === "console") return { ...b, message: undefined };
                        return b;
                    });
                }
                return event;
            },
        });
    }
}

// ── Event tracking (no-ops gracefully when PostHog is not configured) ──

export const analytics = {
    /** Identify a logged-in user (call once after auth). */
    identify(userId: string, traits?: Record<string, unknown>): void {
        if (!posthogReady) return;
        posthog.identify(userId, traits);
    },

    /** Track a named event with optional properties. */
    track(event: string, properties?: Record<string, unknown>): void {
        if (!posthogReady) return;
        posthog.capture(event, properties);
    },

    /** Track a page view (auto-captured, but call for SPA route changes). */
    pageView(path?: string): void {
        if (!posthogReady) return;
        posthog.capture("$pageview", { $current_url: path || window.location.href });
    },

    /** Reset identity on logout. */
    reset(): void {
        if (!posthogReady) return;
        posthog.reset();
    },
};

// ── Pre-defined event helpers (typed, consistent naming) ───────────────

export const Events = {
    querySent: (props: { language?: string; folderId?: string }) =>
        analytics.track("query_sent", props),

    queryCompleted: (props: { creditsUsed?: number; route?: string; latencyMs?: number }) =>
        analytics.track("query_completed", props),

    queryError: (props: { errorType: string; statusCode?: number }) =>
        analytics.track("query_error", props),

    citationClicked: (props: { documentName?: string }) =>
        analytics.track("citation_clicked", props),

    fileUploaded: (props: { fileCount: number; folderId?: string }) =>
        analytics.track("file_uploaded", props),

    dashboardViewed: () =>
        analytics.track("dashboard_viewed"),

    planUpgradeClicked: (props: { currentPlan: string; targetPlan: string }) =>
        analytics.track("plan_upgrade_clicked", props),

    rateLimitHit: (props: { plan: string }) =>
        analytics.track("rate_limit_hit", props),
};
