const ONBOARDING_SEEN_KEY = "evidoc_onboarding_seen";
const SAMPLE_DOCS_KEY = "evidoc_sample_docs_folder";

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

export function markSampleDocsLoaded(folderId: string): void {
    try {
        localStorage.setItem(SAMPLE_DOCS_KEY, folderId);
    } catch { /* best-effort */ }
}

export function getSampleDocsFolderId(): string | null {
    try {
        return localStorage.getItem(SAMPLE_DOCS_KEY);
    } catch {
        return null;
    }
}

export function hasSampleDocsLoaded(): boolean {
    return getSampleDocsFolderId() !== null;
}
