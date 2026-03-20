const ONBOARDING_SEEN_KEY = "evidoc_onboarding_seen";

export function markOnboardingSeen(): void {
    try {
        localStorage.setItem(ONBOARDING_SEEN_KEY, "1");
    } catch { /* best-effort */ }
}

export function hasSeenOnboarding(): boolean {
    try {
        return localStorage.getItem(ONBOARDING_SEEN_KEY) === "1";
    } catch {
        return false;
    }
}
