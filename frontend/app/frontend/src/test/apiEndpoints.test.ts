import { describe, it, expect, vi, beforeEach } from "vitest";
import {
    configApi,
    chatApi,
    getSpeechApi,
    uploadFileApi,
    deleteUploadedFileApi,
    listUploadedFilesApi,
    postChatHistoryApi,
    getChatHistoryListApi,
    getChatHistoryApi,
    deleteChatHistoryApi,
    getHeaders,
    fetchWithNetworkRetry
} from "../api/api";

function mockFetchOnce(body: unknown, status = 200) {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(JSON.stringify(body), { status, statusText: status === 200 ? "OK" : "Error" })
    );
}

function mockFetchError(status: number, statusText: string) {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        new Response(null, { status, statusText })
    );
}

beforeEach(() => {
    vi.restoreAllMocks();
});

describe("getHeaders", () => {
    it("returns empty headers when useLogin is false", async () => {
        const headers = await getHeaders("some-token");
        expect(headers).toEqual({});
    });
});

describe("configApi", () => {
    it("fetches /config and returns Config", async () => {
        const config = { streamingEnabled: true, showVectorOption: false };
        mockFetchOnce(config);
        const result = await configApi();
        expect(result).toEqual(config);
        expect(globalThis.fetch).toHaveBeenCalledWith("/config", expect.objectContaining({ method: "GET" }));
    });
});

describe("chatApi", () => {
    it("posts to /chat when not streaming", async () => {
        mockFetchOnce({ message: { content: "hi", role: "assistant" } });
        const controller = new AbortController();
        await chatApi({ messages: [], context: {}, session_state: null }, false, "token", controller.signal);
        const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
        expect(url).toBe("/chat");
    });

    it("posts to /chat/stream when streaming", async () => {
        mockFetchOnce({ message: { content: "hi", role: "assistant" } });
        const controller = new AbortController();
        await chatApi({ messages: [], context: {}, session_state: null }, true, "token", controller.signal);
        const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
        expect(url).toBe("/chat/stream");
    });
});

describe("getSpeechApi", () => {
    it("returns blob URL on 200", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response("audio", { status: 200, headers: { "Content-Type": "audio/mpeg" } }));
        const result = await getSpeechApi("hello");
        expect(result).toMatch(/^blob:/);
    });

    it("returns null on 400", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(null, { status: 400 }));
        const result = await getSpeechApi("hello");
        expect(result).toBeNull();
    });
});

describe("uploadFileApi", () => {
    it("posts FormData and returns response", async () => {
        mockFetchOnce({ message: "uploaded" });
        const formData = new FormData();
        const result = await uploadFileApi(formData, "token");
        expect(result.message).toBe("uploaded");
    });

    it("throws on failure", async () => {
        mockFetchError(413, "Payload Too Large");
        await expect(uploadFileApi(new FormData(), "token")).rejects.toThrow("Uploading files failed");
    });
});

describe("deleteUploadedFileApi", () => {
    it("sends filename in body", async () => {
        mockFetchOnce({ message: "deleted" });
        await deleteUploadedFileApi("test.pdf", "token");
        const body = JSON.parse(vi.mocked(globalThis.fetch).mock.calls[0][1]!.body as string);
        expect(body.filename).toBe("test.pdf");
    });
});

describe("listUploadedFilesApi", () => {
    it("returns file list", async () => {
        mockFetchOnce(["a.pdf", "b.pdf"]);
        const result = await listUploadedFilesApi("token");
        expect(result).toEqual(["a.pdf", "b.pdf"]);
    });
});

describe("chat history APIs", () => {
    it("postChatHistoryApi sends item", async () => {
        mockFetchOnce({ id: "123" });
        await postChatHistoryApi({ title: "test" }, "token");
        expect(globalThis.fetch).toHaveBeenCalledWith("/chat_history", expect.objectContaining({ method: "POST" }));
    });

    it("getChatHistoryListApi includes count and continuationToken", async () => {
        mockFetchOnce({ sessions: [] });
        await getChatHistoryListApi(20, "ct-abc", "token");
        const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
        expect(url).toContain("count=20");
        expect(url).toContain("continuationToken=ct-abc");
    });

    it("getChatHistoryApi fetches by id", async () => {
        mockFetchOnce({ id: "s1", answers: [] });
        await getChatHistoryApi("s1", "token");
        const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
        expect(url).toContain("/chat_history/sessions/s1");
    });

    it("deleteChatHistoryApi uses DELETE method", async () => {
        vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(null, { status: 204, statusText: "No Content" }));
        // The function checks response.ok, 204 is ok
        await deleteChatHistoryApi("s1", "token");
        expect(globalThis.fetch).toHaveBeenCalledWith(
            expect.stringContaining("/chat_history/sessions/s1"),
            expect.objectContaining({ method: "DELETE" })
        );
    });
});

describe("fetchWithNetworkRetry", () => {
    it("returns response on success without retrying", async () => {
        mockFetchOnce({ ok: true });
        const response = await fetchWithNetworkRetry("/test", { method: "GET" });
        expect(response.status).toBe(200);
        expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    });

    it("retries on TypeError (network error) and succeeds", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch");
        fetchSpy.mockRejectedValueOnce(new TypeError("Load failed"));
        fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));

        const response = await fetchWithNetworkRetry("/test", { method: "GET" }, 1);
        expect(response.status).toBe(200);
        expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    it("retries on 503 status and succeeds", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch");
        fetchSpy.mockResolvedValueOnce(new Response(null, { status: 503 }));
        fetchSpy.mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));

        const response = await fetchWithNetworkRetry("/test", { method: "GET" }, 1);
        expect(response.status).toBe(200);
        expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    it("throws after exhausting retries on persistent TypeError", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch");
        fetchSpy.mockRejectedValue(new TypeError("Failed to fetch"));

        await expect(fetchWithNetworkRetry("/test", { method: "GET" }, 1)).rejects.toThrow("Failed to fetch");
        expect(fetchSpy).toHaveBeenCalledTimes(2); // initial + 1 retry
    });

    it("does not retry on non-retryable errors", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch");
        fetchSpy.mockRejectedValueOnce(new Error("Some other error"));

        await expect(fetchWithNetworkRetry("/test", { method: "GET" }, 2)).rejects.toThrow("Some other error");
        expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    it("does not retry on 4xx status", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch");
        fetchSpy.mockResolvedValueOnce(new Response(null, { status: 400 }));

        const response = await fetchWithNetworkRetry("/test", { method: "GET" }, 2);
        expect(response.status).toBe(400);
        expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    it("does not retry when signal is aborted", async () => {
        const controller = new AbortController();
        controller.abort();
        const fetchSpy = vi.spyOn(globalThis, "fetch");
        fetchSpy.mockRejectedValueOnce(new TypeError("Load failed"));

        await expect(fetchWithNetworkRetry("/test", { method: "GET", signal: controller.signal }, 2)).rejects.toThrow("Load failed");
        expect(fetchSpy).toHaveBeenCalledTimes(1);
    });
});
