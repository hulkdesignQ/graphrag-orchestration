import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Folder24Regular } from "@fluentui/react-icons";
import type { Folder } from "../../api/folders";
import styles from "../../pages/files/Files.module.css";

interface MoveToFolderDialogProps {
    filename: string;
    folders: Folder[];
    currentFolderId: string | null;
    onMove: (filename: string, destFolderId: string | null) => void;
    onDismiss: () => void;
}

export const MoveToFolderDialog = ({ filename, folders, currentFolderId, onMove, onDismiss }: MoveToFolderDialogProps) => {
    const { t } = useTranslation();
    const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);

    const rootFolders = folders.filter(f => !f.parent_folder_id);
    const childrenOf = (parentId: string) => folders.filter(f => f.parent_folder_id === parentId);

    return (
        <div className={styles.overlay} onClick={onDismiss}>
            <div className={styles.dialog} onClick={e => e.stopPropagation()}>
                <h3>{t("files.moveFile")}</h3>
                <p style={{ fontSize: 14, color: "#555", margin: "0 0 12px" }}>{filename}</p>
                <p style={{ fontSize: 13, color: "#888", margin: "0 0 8px" }}>{t("files.selectDestination")}</p>
                <div style={{ maxHeight: 240, overflowY: "auto", border: "1px solid #e5e5e5", borderRadius: 8, marginBottom: 16 }}>
                    {/* Root (no folder) option */}
                    <div
                        style={{
                            padding: "8px 14px",
                            cursor: "pointer",
                            background: selectedFolderId === null ? "#eaf9ff" : "transparent",
                            fontWeight: selectedFolderId === null ? 600 : 400,
                            fontSize: 13,
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                        }}
                        onClick={() => setSelectedFolderId(null)}
                    >
                        🏠 {t("files.rootLevel")}
                    </div>
                    {rootFolders.map(folder => (
                        <div key={folder.id}>
                            <div
                                style={{
                                    padding: "8px 14px",
                                    paddingLeft: 14,
                                    cursor: folder.id === currentFolderId ? "default" : "pointer",
                                    background: selectedFolderId === folder.id ? "#eaf9ff" : "transparent",
                                    fontWeight: selectedFolderId === folder.id ? 600 : 400,
                                    opacity: folder.id === currentFolderId ? 0.5 : 1,
                                    fontSize: 13,
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 8,
                                }}
                                onClick={() => folder.id !== currentFolderId && setSelectedFolderId(folder.id)}
                            >
                                <Folder24Regular /> {folder.name}
                            </div>
                            {childrenOf(folder.id).map(child => (
                                <div
                                    key={child.id}
                                    style={{
                                        padding: "8px 14px",
                                        paddingLeft: 34,
                                        cursor: child.id === currentFolderId ? "default" : "pointer",
                                        background: selectedFolderId === child.id ? "#eaf9ff" : "transparent",
                                        fontWeight: selectedFolderId === child.id ? 600 : 400,
                                        opacity: child.id === currentFolderId ? 0.5 : 1,
                                        fontSize: 13,
                                        display: "flex",
                                        alignItems: "center",
                                        gap: 8,
                                    }}
                                    onClick={() => child.id !== currentFolderId && setSelectedFolderId(child.id)}
                                >
                                    <Folder24Regular /> {child.name}
                                </div>
                            ))}
                        </div>
                    ))}
                </div>
                <div className={styles.dialogActions}>
                    <button className={styles.dialogBtn} onClick={onDismiss}>{t("files.cancel")}</button>
                    <button
                        className={styles.dialogBtnPrimary}
                        onClick={() => onMove(filename, selectedFolderId)}
                        disabled={selectedFolderId === currentFolderId}
                    >
                        {t("files.move")}
                    </button>
                </div>
            </div>
        </div>
    );
};
