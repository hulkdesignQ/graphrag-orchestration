import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Button, Spinner } from "@fluentui/react-components";
import {
    ArrowUpload24Regular,
    Chat24Regular,
    CheckmarkCircle24Regular,
    ArrowRight16Regular,
    DocumentCopy24Regular,
} from "@fluentui/react-icons";
import { useMsal } from "@azure/msal-react";
import { useLogin, getToken } from "../../authConfig";
import { createFolderApi } from "../../api/folders";
import { uploadFilesApi } from "../../api/files";
import { createSampleFiles, SAMPLE_FOLDER_NAME } from "../../utils/sampleDocuments";
import { markOnboardingSeen, hasSampleDocsLoaded, markSampleDocsLoaded } from "../../utils/onboarding";
import styles from "./GettingStarted.module.css";

const GettingStarted = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const client = useLogin ? useMsal().instance : null;

    const [sampleStatus, setSampleStatus] = useState<"idle" | "loading" | "done" | "error">(
        hasSampleDocsLoaded() ? "done" : "idle"
    );
    const [sampleError, setSampleError] = useState("");

    const handleGetStarted = () => {
        markOnboardingSeen();
        navigate("/files");
    };

    const handleGoToChat = () => {
        markOnboardingSeen();
        navigate("/");
    };

    const handleLoadSamples = async () => {
        setSampleStatus("loading");
        setSampleError("");
        try {
            const token = client ? await getToken(client) : undefined;
            if (useLogin && !token) throw new Error("Not authenticated");
            const folder = await createFolderApi({ name: SAMPLE_FOLDER_NAME }, token as string);
            const files = createSampleFiles();
            await uploadFilesApi(files, token as string, undefined, folder.id);
            markSampleDocsLoaded(folder.id);
            markOnboardingSeen();
            setSampleStatus("done");
            setTimeout(() => navigate("/"), 1500);
        } catch (err: unknown) {
            setSampleStatus("error");
            setSampleError(err instanceof Error ? err.message : "Failed to load sample documents");
        }
    };

    const steps = [
        {
            icon: <ArrowUpload24Regular />,
            number: "1",
            title: t("onboarding.step1Title", "Upload your documents"),
            description: t(
                "onboarding.step1Description",
                "Go to Files and upload your PDFs, Word documents, spreadsheets, or images. Evidoc supports 15+ formats. Organize them in folders to query related documents together."
            ),
        },
        {
            icon: <Chat24Regular />,
            number: "2",
            title: t("onboarding.step2Title", "Ask a question"),
            description: t(
                "onboarding.step2Description",
                "Go to Chat, select a folder, and type your question in natural language. Evidoc searches across all documents in the folder using a Knowledge Graph — not just keywords."
            ),
        },
        {
            icon: <CheckmarkCircle24Regular />,
            number: "3",
            title: t("onboarding.step3Title", "Click to verify"),
            description: t(
                "onboarding.step3Description",
                "Every answer includes numbered citations. Click any citation to see the exact sentence highlighted on the original PDF. Verify in seconds — no more manual cross-referencing."
            ),
        },
    ];

    const tips = [
        {
            emoji: "📂",
            text: t("onboarding.tip1", "Group related documents (contract + invoices) in the same folder for cross-document Q&A"),
        },
        {
            emoji: "🎯",
            text: t("onboarding.tip2", "Be specific: \"What is the penalty for late delivery under section 5?\" works better than \"Tell me about penalties\""),
        },
        {
            emoji: "⚖️",
            text: t("onboarding.tip3", "Try comparison questions: \"Do the invoice amounts match the agreed contract rates?\""),
        },
        {
            emoji: "🌍",
            text: t("onboarding.tip4", "Ask in any of 13 languages — Evidoc auto-detects and responds in your language"),
        },
    ];

    return (
        <div className={styles.container}>
            <Helmet>
                <title>{t("onboarding.pageTitle", "Getting Started")} | Evidoc</title>
            </Helmet>

            <div className={styles.hero}>
                <h1 className={styles.heroTitle}>
                    {t("onboarding.heroTitle", "Welcome to Evidoc")}
                </h1>
                <p className={styles.heroSubtitle}>
                    {t("onboarding.heroSubtitle", "Ask your documents anything. Trust every answer with sentence-level, click-to-verify citations.")}
                </p>
            </div>

            <div className={styles.stepsSection}>
                <h2 className={styles.sectionTitle}>
                    {t("onboarding.howItWorks", "How it works")}
                </h2>
                <div className={styles.stepsGrid}>
                    {steps.map((step) => (
                        <div key={step.number} className={styles.stepCard}>
                            <div className={styles.stepNumber}>{step.number}</div>
                            <div className={styles.stepIcon}>{step.icon}</div>
                            <h3 className={styles.stepTitle}>{step.title}</h3>
                            <p className={styles.stepDescription}>{step.description}</p>
                        </div>
                    ))}
                </div>
            </div>

            <div className={styles.tipsSection}>
                <h2 className={styles.sectionTitle}>
                    {t("onboarding.tipsTitle", "Tips for best results")}
                </h2>
                <div className={styles.tipsGrid}>
                    {tips.map((tip, i) => (
                        <div key={i} className={styles.tipCard}>
                            <span className={styles.tipEmoji}>{tip.emoji}</span>
                            <p className={styles.tipText}>{tip.text}</p>
                        </div>
                    ))}
                </div>
            </div>

            <div className={styles.sampleSection}>
                <h2 className={styles.sectionTitle}>
                    {t("onboarding.trySamplesTitle", "Try it now")}
                </h2>
                <p className={styles.sampleDescription}>
                    {t(
                        "onboarding.trySamplesDescription",
                        "Load 3 sample documents — a service agreement, an invoice, and a data policy — then try asking questions across them."
                    )}
                </p>
                {sampleStatus === "idle" && (
                    <Button appearance="primary" size="large" icon={<DocumentCopy24Regular />} onClick={handleLoadSamples}>
                        {t("onboarding.loadSamples", "Load sample documents")}
                    </Button>
                )}
                {sampleStatus === "loading" && (
                    <div className={styles.sampleLoading}>
                        <Spinner size="small" />
                        <span>{t("onboarding.loadingSamples", "Setting up sample documents...")}</span>
                    </div>
                )}
                {sampleStatus === "done" && (
                    <div className={styles.sampleDone}>
                        <CheckmarkCircle24Regular />
                        <span>
                            {t(
                                "onboarding.samplesReady",
                                "Sample documents ready! Select \"Sample Documents\" from the folder dropdown in Chat."
                            )}
                        </span>
                    </div>
                )}
                {sampleStatus === "error" && (
                    <div className={styles.sampleError}>
                        <p>{sampleError}</p>
                        <Button appearance="outline" size="medium" onClick={handleLoadSamples}>
                            {t("onboarding.retryLoad", "Try again")}
                        </Button>
                    </div>
                )}
            </div>

            <div className={styles.actions}>
                <Button appearance="primary" size="large" icon={<ArrowRight16Regular />} iconPosition="after" onClick={handleGetStarted}>
                    {t("onboarding.uploadFirst", "Upload your first document")}
                </Button>
                <Button appearance="outline" size="large" onClick={handleGoToChat}>
                    {t("onboarding.skipToChat", "Go to Chat")}
                </Button>
            </div>
        </div>
    );
};

export default GettingStarted;
