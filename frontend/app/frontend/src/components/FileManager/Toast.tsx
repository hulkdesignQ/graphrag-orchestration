import { CheckmarkCircle24Regular, DismissCircle24Regular, Info24Regular } from "@fluentui/react-icons";
import styles from "../../pages/files/Files.module.css";

interface ToastProps {
    type: "success" | "error" | "info";
    text: string;
    onDismiss: () => void;
}

const TYPE_CLASS: Record<string, string> = {
    success: styles.toastSuccess,
    error: styles.toastError,
    info: styles.toastInfo,
};

const TYPE_ICON: Record<string, React.ReactNode> = {
    success: <CheckmarkCircle24Regular />,
    error: <DismissCircle24Regular />,
    info: <Info24Regular />,
};

export const Toast = ({ type, text, onDismiss }: ToastProps) => (
    <div className={`${styles.toast} ${TYPE_CLASS[type] || ""}`}>
        <span>{TYPE_ICON[type]}</span>
        <span>{text}</span>
        <button className={styles.toastDismiss} onClick={onDismiss}>
            ✕
        </button>
    </div>
);
