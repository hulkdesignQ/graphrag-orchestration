import { useCallback, useRef, useState, DragEvent, ChangeEvent } from "react";
import { useTranslation } from "react-i18next";
import { Clock24Regular, Folder24Regular, ArrowUpload24Regular } from "@fluentui/react-icons";
import styles from "../../pages/files/Files.module.css";

interface UploadZoneProps {
    onUpload: (files: File[]) => void;
    uploading: boolean;
    progress: number;
    acceptedTypes: string;
    uploadedCount?: number;
    uploadTotal?: number;
    disabled?: boolean;
    disabledMessage?: string;
}

export const UploadZone = ({ onUpload, uploading, progress, acceptedTypes, uploadedCount, uploadTotal, disabled, disabledMessage }: UploadZoneProps) => {
    const { t } = useTranslation();
    const [dragOver, setDragOver] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = useCallback((e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(true);
    }, []);

    const handleDragLeave = useCallback((e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragOver(false);
    }, []);

    const handleDrop = useCallback(
        (e: DragEvent) => {
            e.preventDefault();
            e.stopPropagation();
            setDragOver(false);
            const dropped: File[] = Array.from(e.dataTransfer.files);
            if (dropped.length > 0) onUpload(dropped);
        },
        [onUpload]
    );

    const handleBrowse = () => inputRef.current?.click();

    const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            onUpload(Array.from(e.target.files));
            e.target.value = ""; // allow re-selecting same file
        }
    };

    const zoneClass = [
        styles.uploadZone,
        dragOver ? styles.uploadZoneDragOver : "",
        uploading ? styles.uploadZoneUploading : "",
        disabled ? styles.uploadZoneDisabled : "",
    ]
        .filter(Boolean)
        .join(" ");

    return (
        <div
            className={zoneClass}
            onDragOver={disabled ? undefined : handleDragOver}
            onDragLeave={disabled ? undefined : handleDragLeave}
            onDrop={disabled ? undefined : handleDrop}
            onClick={disabled ? undefined : handleBrowse}
            role="button"
            tabIndex={disabled ? -1 : 0}
            onKeyDown={disabled ? undefined : (e) => e.key === "Enter" && handleBrowse()}
            aria-disabled={disabled}
            title={disabled ? disabledMessage : undefined}
        >
            <span className={styles.uploadIcon}>{uploading ? <Clock24Regular /> : disabled ? <Folder24Regular /> : <ArrowUpload24Regular />}</span>
            {uploading ? (
                <>
                    <p className={styles.uploadText}>
                        {uploadTotal && uploadTotal > 1
                            ? t("files.uploadingProgress", { current: Math.min((uploadedCount ?? 0) + 1, uploadTotal), total: uploadTotal })
                            : t("files.uploading")}
                    </p>
                    <div className={styles.progressBarOuter}>
                        <div className={styles.progressBarInner} style={{ width: `${progress}%` }} />
                    </div>
                    <p className={styles.progressLabel}>{progress}%</p>
                </>
            ) : disabled ? (
                <>
                    <p className={styles.uploadText}>{disabledMessage || t("files.selectFolderFirst")}</p>
                    <p className={styles.uploadTextSub}>{t("files.selectFolderHint")}</p>
                </>
            ) : (
                <>
                    <p className={styles.uploadText}>{t("files.dragDropFiles")}</p>
                    <p className={styles.uploadTextSub}>{t("files.orClickBrowse")}</p>
                    <p className={styles.uploadFormatsHint}>{t("files.supportedFormats")}</p>
                    <button className={styles.uploadBrowseBtn} onClick={(e) => { e.stopPropagation(); handleBrowse(); }}>
                        {t("files.chooseFiles")}
                    </button>
                </>
            )}
            <input
                ref={inputRef}
                type="file"
                multiple
                accept={acceptedTypes}
                style={{ display: "none" }}
                onChange={handleInputChange}
            />
        </div>
    );
};
