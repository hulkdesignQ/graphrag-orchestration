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
});
