/**
 * Billing API client — Stripe Checkout + subscription management.
 *
 * Talks to /billing/* endpoints on the API gateway.
 */

import { getHeaders, fetchWithAuthRetry } from "./api";

// ============================================================================
// Types
// ============================================================================

export interface BillingConfig {
    stripe_enabled: boolean;
    publishable_key: string | null;
}

export interface CheckoutResponse {
    checkout_url: string;
}

export interface PortalResponse {
    portal_url: string;
}

export interface SubscriptionStatus {
    has_subscription: boolean;
    plan: string;
    status: string;
    stripe_customer_id: string | null;
    current_period_end: string | null;
    cancel_at_period_end: boolean;
    manage_url: string | null;
}

// ============================================================================
// API calls
// ============================================================================

/** Fetch billing configuration (Stripe enabled + publishable key). */
export async function fetchBillingConfig(): Promise<BillingConfig> {
    try {
        const response = await fetch("/billing/config", { method: "GET" });
        if (!response.ok) {
            console.warn(`[billing] /billing/config returned ${response.status}`);
            return { stripe_enabled: false, publishable_key: null };
        }
        return response.json();
    } catch (err) {
        console.warn("[billing] Failed to fetch billing config:", err);
        return { stripe_enabled: false, publishable_key: null };
    }
}

/** Create a Stripe Checkout session and return the redirect URL. */
export async function createCheckoutSession(
    targetPlan: string,
    idToken: string | undefined
): Promise<CheckoutResponse> {
    const headers = await getHeaders(idToken);
    const response = await fetchWithAuthRetry("/billing/create-checkout-session", {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ plan: targetPlan }),
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(err.detail || `Checkout failed: ${response.status}`);
    }
    return response.json();
}

/** Create a Stripe Billing Portal session and return the redirect URL. */
export async function createPortalSession(
    idToken: string | undefined
): Promise<PortalResponse> {
    const headers = await getHeaders(idToken);
    const response = await fetchWithAuthRetry("/billing/create-portal-session", {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(err.detail || `Portal session failed: ${response.status}`);
    }
    return response.json();
}

/** Fetch current subscription status. */
export async function fetchSubscription(
    idToken: string | undefined
): Promise<SubscriptionStatus> {
    const headers = await getHeaders(idToken);
    const response = await fetchWithAuthRetry("/billing/subscription", {
        method: "GET",
        headers: { ...headers, "Content-Type": "application/json" },
    });
    if (!response.ok) {
        return {
            has_subscription: false,
            plan: "free",
            status: "none",
            stripe_customer_id: null,
            current_period_end: null,
            cancel_at_period_end: false,
            manage_url: null,
        };
    }
    return response.json();
}
