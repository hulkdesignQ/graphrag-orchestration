import { useState, useCallback } from "react";
import { Button, Link, tokens } from "@fluentui/react-components";
import { ShieldCheckmark24Regular } from "@fluentui/react-icons";
import { useTranslation } from "react-i18next";
import { initAnalytics, shutdownAnalytics } from "../../analytics";
import styles from "./CookieConsentBanner.module.css";

const CONSENT_KEY = "evidoc_cookie_consent";

export type ConsentValue = "all" | "necessary" | null;

export function getStoredConsent(): ConsentValue {
    try {
        const v = localStorage.getItem(CONSENT_KEY);
        if (v === "all" || v === "necessary") return v;
    } catch {
        /* localStorage unavailable */
    }
    return null;
}

function storeConsent(value: "all" | "necessary"): void {
    try {
        localStorage.setItem(CONSENT_KEY, value);
    } catch {
        /* best-effort */
    }
}

export const CookieConsentBanner = () => {
    const { t } = useTranslation();
    const [visible, setVisible] = useState<boolean>(getStoredConsent() === null);

    const accept = useCallback((choice: "all" | "necessary") => {
        storeConsent(choice);
        if (choice === "all") {
            initAnalytics();
        } else {
            shutdownAnalytics();
        }
        setVisible(false);
    }, []);

    if (!visible) return null;

    return (
        <div className={styles.overlay}>
            <div className={styles.banner}>
                <div className={styles.icon}>
                    <ShieldCheckmark24Regular primaryFill={tokens.colorBrandForeground1} />
                </div>
                <div className={styles.content}>
                    <p className={styles.title}>
                        {t("cookieConsent.title", "We respect your privacy")}
                    </p>
                    <p className={styles.description}>
                        {t(
                            "cookieConsent.description",
                            "We use essential cookies for authentication and preferences. Optional analytics cookies help us improve Evidoc. No document content is ever collected by analytics."
                        )}
                        {" "}
                        <Link href="/docs/legal/COOKIE_POLICY.md" target="_blank" inline>
                            {t("cookieConsent.learnMore", "Learn more")}
                        </Link>
                    </p>
                </div>
                <div className={styles.actions}>
                    <Button appearance="primary" onClick={() => accept("all")}>
                        {t("cookieConsent.acceptAll", "Accept all")}
                    </Button>
                    <Button appearance="outline" onClick={() => accept("necessary")}>
                        {t("cookieConsent.necessaryOnly", "Necessary only")}
                    </Button>
                </div>
            </div>
        </div>
    );
};
