const BACKEND_URI = "";

import { ChatAppResponse, ChatAppResponseOrError, ChatAppRequest, Config, SimpleAPIResponse, HistoryListApiResponse, HistoryApiResponse } from "./models";
import { useLogin, getToken, isUsingAppServicesLogin } from "../authConfig";

let isRefreshingAuth = false;
let authRefreshPromise: Promise<boolean> | null = null;

/**
 * Attempt to refresh the EasyAuth session token via the /.auth/refresh endpoint.
 * Uses a singleton pattern to prevent multiple simultaneous refresh attempts.
 * Returns true if refresh succeeded, false otherwise.
 */
async function refreshEasyAuthToken(): Promise<boolean> {
    if (isRefreshingAuth && authRefreshPromise) {
        return authRefreshPromise;
    }
    isRefreshingAuth = true;
    authRefreshPromise = (async () => {
        try {
            const resp = await fetch(".auth/refresh");
            return resp.ok;
        } catch {
            return false;
        } finally {
            isRefreshingAuth = false;
            authRefreshPromise = null;
        }
    })();
    return authRefreshPromise;
}

/**
 * Returns true for errors that are likely transient and worth retrying:
 * - TypeError from fetch() (network break, DNS failure, CORS during outage)
 * - HTTP 502, 503, 504 (upstream/gateway errors, often transient)
 */
function isRetryableError(error: unknown): boolean {
    return error instanceof TypeError;
}

function isRetryableStatus(status: number): boolean {
    return status === 502 || status === 503 || status === 504;
}

/**
 * Fetch with automatic retry for transient network errors.
 * Uses exponential backoff with jitter: ~1s, ~2s (max 2 retries).
 * Respects AbortSignal — stops retrying if the request was cancelled.
 */
export async function fetchWithNetworkRetry(url: string, init: RequestInit, maxRetries = 2): Promise<Response> {
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch(url, init);
            if (isRetryableStatus(response.status) && attempt < maxRetries && !init.signal?.aborted) {
                await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt) + Math.random() * 500));
                continue;
            }
            return response;
        } catch (e) {
            if (isRetryableError(e) && attempt < maxRetries && !init.signal?.aborted) {
                await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt) + Math.random() * 500));
                continue;
            }
            throw e;
        }
    }
    // Unreachable, but satisfies TypeScript
    return fetch(url, init);
}

/**
 * Wrapper around fetch that:
 * 1. Retries on transient network errors (TypeError) and 5xx with exponential backoff
 * 2. Retries once on 401 after refreshing the EasyAuth token
 */
export async function fetchWithAuthRetry(url: string, init: RequestInit): Promise<Response> {
    const response = await fetchWithNetworkRetry(url, init);

    if (response.status === 401 && isUsingAppServicesLogin) {
        // Invalidate stale cached token so refresh fetches a new one
        globalThis.cachedAppServicesToken = null;

        const refreshed = await refreshEasyAuthToken();
        if (refreshed) {
            // Rebuild headers with the fresh token from .auth/me
            const freshHeaders = await getHeaders(undefined);
            const retryInit: RequestInit = {
                ...init,
                headers: { ...freshHeaders, "Content-Type": "application/json" }
            };
            return fetchWithNetworkRetry(url, retryInit);
        }
        // Refresh failed — redirect to fresh login
        window.location.href = ".auth/login/aad?post_login_redirect_uri=" + encodeURIComponent(window.location.pathname + window.location.search);
    }

    return response;
}

export async function getHeaders(idToken: string | undefined): Promise<Record<string, string>> {
    // If using login and not using app services, add the id token of the logged in account as the authorization
    if (useLogin && !isUsingAppServicesLogin) {
        if (idToken) {
            return { Authorization: `Bearer ${idToken}` };
        }
    }

    return {};
}

export async function configApi(): Promise<Config> {
    const response = await fetch(`${BACKEND_URI}/config`, {
        method: "GET"
    });

    return (await response.json()) as Config;
}

export async function chatApi(request: ChatAppRequest, shouldStream: boolean, idToken: string | undefined, signal: AbortSignal): Promise<Response> {
    let url = `${BACKEND_URI}/chat`;
    if (shouldStream) {
        url += "/stream";
    }
    const headers = await getHeaders(idToken);
    return await fetchWithAuthRetry(url, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(request),
        signal: signal
    });
}

export type SpeechTokenResponse = {
    token: string;
    region: string;
    languages: string[];
};

export async function getSpeechTokenApi(): Promise<SpeechTokenResponse | null> {
    try {
        const response = await fetch("/speech/token", { method: "GET" });
        if (response.ok) {
            return (await response.json()) as SpeechTokenResponse;
        }
        console.warn("Speech token not available:", response.status);
        return null;
    } catch {
        return null;
    }
}

export async function getSpeechApi(text: string): Promise<string | null> {
    return await fetch("/speech", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            text: text
        })
    })
        .then(response => {
            if (response.status == 200) {
                return response.blob();
            } else if (response.status == 400) {
                console.log("Speech synthesis is not enabled.");
                return null;
            } else {
                console.error("Unable to get speech synthesis.");
                return null;
            }
        })
        .then(blob => (blob ? URL.createObjectURL(blob) : null));
}

export async function reportSpeechUsage(characters: number, detectedLanguage?: string): Promise<void> {
    try {
        await fetch("/speech/usage", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ characters, detected_language: detectedLanguage })
        });
    } catch {
        // Fire-and-forget: don't block on tracking failures
    }
}

/**
 * Build the /content/<filename> URL for a citation.
 * When documentUrl (full blob URL) is available, extract the filename from it
 * so the extension (e.g. ".pdf") is preserved — document_title has it stripped.
 */
export function getCitationFilePath(citation: string, documentUrl?: string): string {
    let filename = citation;
    if (documentUrl) {
        try {
            // Extract last path segment: ".../test-docs/PROPERTY%20MANAGEMENT%20AGREEMENT.pdf" → decoded filename
            const urlPath = new URL(documentUrl).pathname;
            const lastSegment = urlPath.split("/").filter(Boolean).pop();
            if (lastSegment) {
                filename = decodeURIComponent(lastSegment);
            }
        } catch {
            // If URL parsing fails, fall through to use citation as-is
        }
    }
    // Remove only the last parenthesized suffix (e.g., "(page 3)")
    const cleanedCitation = filename.replace(/\s*\([^)]*\)\s*$/, "").trim();

    // If no documentUrl and no file extension, this is likely a community/graph
    // citation (not a real file). Return empty so the UI doesn't try to fetch it.
    const hasFileExtension = /\.\w{2,5}$/.test(cleanedCitation);
    if (!documentUrl && !hasFileExtension) {
        return "";
    }

    let url = `${BACKEND_URI}/content/${encodeURIComponent(cleanedCitation)}`;
    // Pass the original blob URL so the backend can proxy from it directly
    if (documentUrl) {
        url += `?source=${encodeURIComponent(documentUrl)}`;
    }
    return url;
}

export async function uploadFileApi(request: FormData, idToken: string): Promise<SimpleAPIResponse> {
    const response = await fetchWithAuthRetry("/upload", {
        method: "POST",
        headers: await getHeaders(idToken),
        body: request
    });

    if (!response.ok) {
        throw new Error(`Uploading files failed: ${response.statusText}`);
    }

    const dataResponse: SimpleAPIResponse = await response.json();
    return dataResponse;
}

export async function deleteUploadedFileApi(filename: string, idToken: string): Promise<SimpleAPIResponse> {
    const headers = await getHeaders(idToken);
    const response = await fetchWithAuthRetry("/delete_uploaded", {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ filename })
    });

    if (!response.ok) {
        throw new Error(`Deleting file failed: ${response.statusText}`);
    }

    const dataResponse: SimpleAPIResponse = await response.json();
    return dataResponse;
}

export async function listUploadedFilesApi(idToken: string): Promise<string[]> {
    const response = await fetchWithAuthRetry(`/list_uploaded`, {
        method: "GET",
        headers: await getHeaders(idToken)
    });

    if (!response.ok) {
        throw new Error(`Listing files failed: ${response.statusText}`);
    }

    const dataResponse: string[] = await response.json();
    return dataResponse;
}

export async function postChatHistoryApi(item: any, idToken: string): Promise<any> {
    const headers = await getHeaders(idToken);
    const response = await fetchWithAuthRetry("/chat_history", {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(item)
    });

    if (!response.ok) {
        throw new Error(`Posting chat history failed: ${response.statusText}`);
    }

    const dataResponse: any = await response.json();
    return dataResponse;
}

export async function getChatHistoryListApi(count: number, continuationToken: string | undefined, idToken: string): Promise<HistoryListApiResponse> {
    const headers = await getHeaders(idToken);
    let url = `${BACKEND_URI}/chat_history/sessions?count=${count}`;
    if (continuationToken) {
        url += `&continuationToken=${continuationToken}`;
    }

    const response = await fetchWithAuthRetry(url.toString(), {
        method: "GET",
        headers: { ...headers, "Content-Type": "application/json" }
    });

    if (!response.ok) {
        throw new Error(`Getting chat histories failed: ${response.statusText}`);
    }

    const dataResponse: HistoryListApiResponse = await response.json();
    return dataResponse;
}

export async function getChatHistoryApi(id: string, idToken: string): Promise<HistoryApiResponse> {
    const headers = await getHeaders(idToken);
    const response = await fetchWithAuthRetry(`/chat_history/sessions/${id}`, {
        method: "GET",
        headers: { ...headers, "Content-Type": "application/json" }
    });

    if (!response.ok) {
        throw new Error(`Getting chat history failed: ${response.statusText}`);
    }

    const dataResponse: HistoryApiResponse = await response.json();
    return dataResponse;
}

export async function deleteChatHistoryApi(id: string, idToken: string): Promise<any> {
    const headers = await getHeaders(idToken);
    const response = await fetchWithAuthRetry(`/chat_history/sessions/${id}`, {
        method: "DELETE",
        headers: { ...headers, "Content-Type": "application/json" }
    });

    if (!response.ok) {
        throw new Error(`Deleting chat history failed: ${response.statusText}`);
    }
}
