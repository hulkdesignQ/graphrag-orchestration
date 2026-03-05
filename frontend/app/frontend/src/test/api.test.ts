import { describe, it, expect } from "vitest";
import { getCitationFilePath } from "../api/api";

describe("getCitationFilePath", () => {
    it("returns content path for simple filename", () => {
        expect(getCitationFilePath("report.pdf")).toBe("/content/report.pdf");
    });

    it("strips last parenthesized suffix", () => {
        expect(getCitationFilePath("report.pdf (page 3)")).toBe("/content/report.pdf");
    });

    it("only strips the last parenthesized group, preserving parentheses in filename", () => {
        expect(getCitationFilePath("report (v2).pdf (section 1)")).toBe("/content/report%20(v2).pdf");
    });

    it("handles citation with no parentheses", () => {
        expect(getCitationFilePath("my-file.docx")).toBe("/content/my-file.docx");
    });

    it("encodes spaces and special characters", () => {
        expect(getCitationFilePath("my file.pdf")).toBe("/content/my%20file.pdf");
    });

    it("extracts filename from documentUrl when provided", () => {
        expect(
            getCitationFilePath("PROPERTY MANAGEMENT AGREEMENT", "https://storage.blob.core.windows.net/test-docs/PROPERTY%20MANAGEMENT%20AGREEMENT.pdf")
        ).toBe("/content/PROPERTY%20MANAGEMENT%20AGREEMENT.pdf");
    });

    it("uses citation as fallback when documentUrl is invalid", () => {
        expect(getCitationFilePath("report.pdf", "not-a-url")).toBe("/content/report.pdf");
    });

    it("uses citation as fallback when documentUrl has no path segments", () => {
        expect(getCitationFilePath("report.pdf", "https://example.com")).toBe("/content/report.pdf");
    });

    it("handles documentUrl with encoded special characters", () => {
        expect(
            getCitationFilePath("Agreement", "https://storage.blob.core.windows.net/docs/My%20Report%20(v2).pdf")
        ).toBe("/content/My%20Report%20(v2).pdf");
    });
});
