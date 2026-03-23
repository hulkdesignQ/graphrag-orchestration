import { describe, it, expect } from "vitest";
import { formatFileSize, getFileExtension, getFileContentUrl } from "../api/files";

describe("formatFileSize", () => {
    it("returns dash for undefined", () => {
        expect(formatFileSize(undefined)).toBe("—");
    });

    it("returns '0 B' for 0 bytes", () => {
        expect(formatFileSize(0)).toBe("0 B");
    });

    it("formats bytes", () => {
        expect(formatFileSize(500)).toBe("500 B");
    });

    it("formats kilobytes", () => {
        expect(formatFileSize(1024)).toBe("1.0 KB");
        expect(formatFileSize(1536)).toBe("1.5 KB");
    });

    it("formats megabytes", () => {
        expect(formatFileSize(1048576)).toBe("1.0 MB");
        expect(formatFileSize(5242880)).toBe("5.0 MB");
    });

    it("formats gigabytes", () => {
        expect(formatFileSize(1073741824)).toBe("1.0 GB");
    });
});

describe("getFileExtension", () => {
    it("extracts extension", () => {
        expect(getFileExtension("doc.pdf")).toBe("pdf");
    });

    it("lowercases extension", () => {
        expect(getFileExtension("DOC.PDF")).toBe("pdf");
    });

    it("handles multiple dots", () => {
        expect(getFileExtension("my.file.txt")).toBe("txt");
    });

    it("returns empty for no extension", () => {
        expect(getFileExtension("README")).toBe("readme");
    });
});

describe("getFileContentUrl", () => {
    it("encodes the path", () => {
        expect(getFileContentUrl("my file.pdf")).toBe("/content/my%20file.pdf");
    });

    it("encodes special characters", () => {
        expect(getFileContentUrl("report (1).pdf")).toBe("/content/report%20(1).pdf");
    });

    it("appends folder as query param when provided", () => {
        expect(getFileContentUrl("report.pdf", "invoices")).toBe("/content/report.pdf?folder=invoices");
    });

    it("encodes folder name with spaces", () => {
        expect(getFileContentUrl("report.pdf", "my folder")).toBe("/content/report.pdf?folder=my%20folder");
    });
});
