import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useFileBlob } from "../../hooks/useFileBlob";
import { PdfHighlightViewer } from "../DocumentViewer/PdfHighlightViewer";
import { getFileContentUrl } from "../../api/files";
import { useMsal } from "@azure/msal-react";
import { useLogin, getToken } from "../../authConfig";
import { getHeaders } from "../../api/api";
import DOMPurify from "dompurify";
import styles from "./FilePreviewModal.module.css";

interface Props {
    filename: string;
    /** All filenames in the current list — enables prev/next navigation */
    allFiles: string[];
    onDismiss: () => void;
    /** Navigate to a different file */
    onNavigate: (filename: string) => void;
}

type FileCategory = "pdf" | "image" | "html" | "docx" | "xlsx" | "pptx" | "text" | "unknown";

function getCategory(filename: string): FileCategory {
    const ext = filename.split(".").pop()?.toLowerCase() || "";
    if (ext === "pdf") return "pdf";
    if (["png", "jpg", "jpeg", "bmp", "tiff", "tif", "gif", "webp"].includes(ext)) return "image";
    if (["html", "htm"].includes(ext)) return "html";
    if (ext === "docx") return "docx";
    if (ext === "xlsx" || ext === "xls") return "xlsx";
    if (ext === "pptx" || ext === "ppt") return "pptx";
    if (["txt", "csv", "json", "xml", "md", "log"].includes(ext)) return "text";
    return "unknown";
}

export const FilePreviewModal = ({ filename, allFiles, onDismiss, onNavigate }: Props) => {
    const { t } = useTranslation();
    const { blobUrl, rawBytes, contentType, loading, error } = useFileBlob(filename);
    const category = useMemo(() => getCategory(filename), [filename]);

    // Zoom/pan state
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const dragging = useRef(false);
    const dragStart = useRef({ x: 0, y: 0 });
    const panStart = useRef({ x: 0, y: 0 });

    // Reset zoom on file change
    useEffect(() => {
        setZoom(1);
        setPan({ x: 0, y: 0 });
    }, [filename]);

    // File navigation
    const currentIndex = allFiles.indexOf(filename);
    const hasPrev = currentIndex > 0;
    const hasNext = currentIndex < allFiles.length - 1;
    const goPrev = () => hasPrev && onNavigate(allFiles[currentIndex - 1]);
    const goNext = () => hasNext && onNavigate(allFiles[currentIndex + 1]);

    // Keyboard shortcuts
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (e.key === "Escape") onDismiss();
            else if (e.key === "ArrowLeft") goPrev();
            else if (e.key === "ArrowRight") goNext();
            else if (e.key === "+" || e.key === "=") setZoom(z => Math.min(5, z + 0.25));
            else if (e.key === "-") setZoom(z => Math.max(0.25, z - 0.25));
            else if (e.key === "0") { setZoom(1); setPan({ x: 0, y: 0 }); }
        };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    });

    // Scroll wheel zoom
    const handleWheel = useCallback((e: React.WheelEvent) => {
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            const delta = e.deltaY > 0 ? -0.15 : 0.15;
            setZoom(z => Math.max(0.25, Math.min(5, z + delta)));
        }
    }, []);

    // Pan via drag
    const handleMouseDown = useCallback((e: React.MouseEvent) => {
        if (zoom > 1) {
            dragging.current = true;
            dragStart.current = { x: e.clientX, y: e.clientY };
            panStart.current = { ...pan };
        }
    }, [zoom, pan]);

    const handleMouseMove = useCallback((e: React.MouseEvent) => {
        if (dragging.current) {
            setPan({
                x: panStart.current.x + (e.clientX - dragStart.current.x),
                y: panStart.current.y + (e.clientY - dragStart.current.y),
            });
        }
    }, []);

    const handleMouseUp = useCallback(() => {
        dragging.current = false;
    }, []);

    // Download
    const handleDownload = useCallback(() => {
        if (blobUrl) {
            const a = document.createElement("a");
            a.href = blobUrl;
            a.download = filename;
            a.click();
        }
    }, [blobUrl, filename]);

    // Close on backdrop click
    const handleBackdropClick = useCallback((e: React.MouseEvent) => {
        if (e.target === e.currentTarget) onDismiss();
    }, [onDismiss]);

    const zoomPercent = Math.round(zoom * 100);

    return (
        <div className={styles.overlay} onClick={handleBackdropClick}>
            {/* Top bar */}
            <div className={styles.topBar}>
                <span className={styles.filename} title={filename}>{filename}</span>
                {allFiles.length > 1 && (
                    <span className={styles.navInfo}>
                        {currentIndex + 1} / {allFiles.length}
                    </span>
                )}
                <button className={styles.topBtn} onClick={goPrev} disabled={!hasPrev} title={t("preview.prev")}>◀</button>
                <button className={styles.topBtn} onClick={goNext} disabled={!hasNext} title={t("preview.next")}>▶</button>
                <button className={styles.topBtn} onClick={handleDownload} disabled={!blobUrl} title={t("preview.download")}>
                    ⬇ {t("preview.download")}
                </button>
                <button className={styles.topBtn} onClick={onDismiss} title={t("preview.close")}>✕</button>
            </div>

            {/* Zoom bar */}
            {(category === "image" || category === "pdf") && (
                <div className={styles.zoomBar}>
                    <button className={styles.zoomBtn} onClick={() => setZoom(z => Math.max(0.25, z - 0.25))}>−</button>
                    <span className={styles.zoomLevel}>{zoomPercent}%</span>
                    <button className={styles.zoomBtn} onClick={() => setZoom(z => Math.min(5, z + 0.25))}>+</button>
                    <button className={styles.zoomBtn} onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}>
                        {t("preview.fitWidth")}
                    </button>
                </div>
            )}

            {/* Content */}
            <div
                className={styles.viewerArea}
                onWheel={handleWheel}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
            >
                {loading && (
                    <div className={styles.stateCard}>
                        <div className={styles.spinner} />
                        <h3>{t("preview.loading")}</h3>
                    </div>
                )}

                {error && (
                    <div className={styles.stateCard}>
                        <h3 className={styles.errorText}>{t("preview.error")}</h3>
                        <p>{error}</p>
                    </div>
                )}

                {!loading && !error && blobUrl && (
                    <div
                        className={styles.viewerContent}
                        style={{ transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})` }}
                    >
                        <ContentRenderer
                            category={category}
                            blobUrl={blobUrl}
                            rawBytes={rawBytes}
                            contentType={contentType}
                            filename={filename}
                        />
                    </div>
                )}
            </div>
        </div>
    );
};

/* ---- Format-specific renderers ---- */

interface RendererProps {
    category: FileCategory;
    blobUrl: string;
    rawBytes: ArrayBuffer | null;
    contentType: string | null;
    filename: string;
}

const ContentRenderer = ({ category, blobUrl, rawBytes, contentType, filename }: RendererProps) => {
    switch (category) {
        case "pdf":
            return <PdfHighlightViewer src={blobUrl} highlights={[]} height="calc(100vh - 100px)" />;
        case "image":
            return <ImageRenderer blobUrl={blobUrl} filename={filename} />;
        case "html":
            return <HtmlRenderer rawBytes={rawBytes} />;
        case "docx":
            return <DocxRenderer rawBytes={rawBytes} />;
        case "xlsx":
            return <XlsxRenderer rawBytes={rawBytes} />;
        case "pptx":
            return <FallbackRenderer filename={filename} blobUrl={blobUrl} />;
        case "text":
            return <TextRenderer rawBytes={rawBytes} />;
        default:
            return <FallbackRenderer filename={filename} blobUrl={blobUrl} />;
    }
};

/* Image */
const ImageRenderer = ({ blobUrl, filename }: { blobUrl: string; filename: string }) => (
    <img src={blobUrl} alt={filename} className={styles.previewImage} draggable={false} />
);

/* HTML */
const HtmlRenderer = ({ rawBytes }: { rawBytes: ArrayBuffer | null }) => {
    const html = useMemo(() => {
        if (!rawBytes) return "";
        const text = new TextDecoder().decode(rawBytes);
        return DOMPurify.sanitize(text, { WHOLE_DOCUMENT: true, ADD_TAGS: ["style"] });
    }, [rawBytes]);

    return <iframe srcDoc={html} className={styles.htmlFrame} sandbox="allow-same-origin" title="HTML Preview" />;
};

/* Plain text */
const TextRenderer = ({ rawBytes }: { rawBytes: ArrayBuffer | null }) => {
    const text = useMemo(() => {
        if (!rawBytes) return "";
        return new TextDecoder().decode(rawBytes);
    }, [rawBytes]);

    return (
        <div style={{ background: "#fff", padding: 24, borderRadius: 8, maxWidth: "90vw", overflow: "auto", maxHeight: "80vh" }}>
            <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-word", fontSize: 13, lineHeight: 1.6 }}>{text}</pre>
        </div>
    );
};

/* DOCX via mammoth (lazy-loaded) */
const DocxRenderer = ({ rawBytes }: { rawBytes: ArrayBuffer | null }) => {
    const { t } = useTranslation();
    const [html, setHtml] = useState<string | null>(null);
    const [err, setErr] = useState<string | null>(null);

    useEffect(() => {
        if (!rawBytes) return;
        let cancelled = false;

        (async () => {
            try {
                const mammoth = await import("mammoth");
                const result = await mammoth.convertToHtml({ arrayBuffer: rawBytes });
                if (!cancelled) {
                    setHtml(DOMPurify.sanitize(result.value, { WHOLE_DOCUMENT: true, ADD_TAGS: ["style"] }));
                }
            } catch (e: any) {
                if (!cancelled) setErr(e.message || "Failed to render DOCX");
            }
        })();

        return () => { cancelled = true; };
    }, [rawBytes]);

    if (err) return <div className={styles.stateCard}><h3 className={styles.errorText}>{t("preview.error")}</h3><p>{err}</p></div>;
    if (!html) return <div className={styles.stateCard}><div className={styles.spinner} /><h3>{t("preview.rendering")}</h3></div>;
    return <iframe srcDoc={html} className={styles.htmlFrame} sandbox="allow-same-origin" title="DOCX Preview" />;
};

/* XLSX via SheetJS (lazy-loaded) */
const XlsxRenderer = ({ rawBytes }: { rawBytes: ArrayBuffer | null }) => {
    const { t } = useTranslation();
    const [tableHtml, setTableHtml] = useState<string | null>(null);
    const [err, setErr] = useState<string | null>(null);

    useEffect(() => {
        if (!rawBytes) return;
        let cancelled = false;

        (async () => {
            try {
                const XLSX = await import("xlsx");
                const wb = XLSX.read(rawBytes, { type: "array" });
                const firstSheet = wb.Sheets[wb.SheetNames[0]];
                const html = XLSX.utils.sheet_to_html(firstSheet);
                if (!cancelled) setTableHtml(html);
            } catch (e: any) {
                if (!cancelled) setErr(e.message || "Failed to render spreadsheet");
            }
        })();

        return () => { cancelled = true; };
    }, [rawBytes]);

    if (err) return <div className={styles.stateCard}><h3 className={styles.errorText}>{t("preview.error")}</h3><p>{err}</p></div>;
    if (!tableHtml) return <div className={styles.stateCard}><div className={styles.spinner} /><h3>{t("preview.rendering")}</h3></div>;
    return <div className={styles.xlsxWrapper} dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(tableHtml) }} />;
};

/* Fallback with download button */
const FallbackRenderer = ({ filename, blobUrl }: { filename: string; blobUrl: string }) => {
    const { t } = useTranslation();
    const handleDownload = () => {
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = filename;
        a.click();
    };

    return (
        <div className={styles.stateCard}>
            <h3>{t("preview.noPreview")}</h3>
            <p>{t("preview.noPreviewHint")}</p>
            <button className={styles.downloadBtn} onClick={handleDownload}>
                ⬇ {t("preview.downloadFile")}
            </button>
        </div>
    );
};
