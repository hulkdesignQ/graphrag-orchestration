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
    ArrowLeft16Regular,
    DocumentCopy24Regular,
} from "@fluentui/react-icons";
import { useMsal } from "@azure/msal-react";
import { useLogin, getToken } from "../../authConfig";
import { createFolderApi } from "../../api/folders";
import { uploadFilesApi } from "../../api/files";
import { createSampleFiles, SAMPLE_FOLDER_NAME } from "../../utils/sampleDocuments";
import { markOnboardingSeen, hasSampleDocsLoaded, markSampleDocsLoaded } from "../../utils/onboarding";
import styles from "./GettingStarted.module.css";

const STEP_COUNT = 3;

const GettingStarted = () => {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const client = useLogin ? useMsal().instance : null;

    const [activeStep, setActiveStep] = useState(0);
    const [sampleStatus, setSampleStatus] = useState<"idle" | "loading" | "done" | "error">(
        hasSampleDocsLoaded() ? "done" : "idle"
    );
    const [sampleError, setSampleError] = useState("");

    const handleFinish = () => {
        markOnboardingSeen();
        navigate("/");
    };

    const handleGoToFiles = () => {
        markOnboardingSeen();
        navigate("/files");
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
            setSampleStatus("done");
        } catch (err: unknown) {
            setSampleStatus("error");
            setSampleError(err instanceof Error ? err.message : "Failed to load sample documents");
        }
    };

    const stepMeta = [
        { label: t("onboarding.tabWelcome", "Welcome"), icon: "👋" },
        { label: t("onboarding.tabUpload", "Upload"), icon: "📄" },
        { label: t("onboarding.tabAsk", "Ask & Verify"), icon: "💬" },
    ];

    /* ── Step content renderers ── */

    const renderStep0 = () => (
        <div className={styles.stepContent}>
            <div className={styles.stepHero}>
                <h1 className={styles.heroTitle}>
                    {t("onboarding.heroTitle", "Welcome to Evidoc")}
                </h1>
                <p className={styles.heroSubtitle}>
                    {t("onboarding.heroSubtitle", "Ask your documents anything. Trust every answer with sentence-level, click-to-verify citations.")}
                </p>
            </div>

            <div className={styles.featureList}>
                <div className={styles.featureItem}>
                    <span className={styles.featureIcon}><ArrowUpload24Regular /></span>
                    <div>
                        <strong>{t("onboarding.feature1Title", "Upload any document")}</strong>
                        <p>{t("onboarding.feature1Desc", "PDFs, Word, Excel, images — 15+ formats supported")}</p>
                    </div>
                </div>
                <div className={styles.featureItem}>
                    <span className={styles.featureIcon}><Chat24Regular /></span>
                    <div>
                        <strong>{t("onboarding.feature2Title", "Ask in natural language")}</strong>
                        <p>{t("onboarding.feature2Desc", "Knowledge Graph search — not just keywords")}</p>
                    </div>
                </div>
                <div className={styles.featureItem}>
                    <span className={styles.featureIcon}><CheckmarkCircle24Regular /></span>
                    <div>
                        <strong>{t("onboarding.feature3Title", "Click-to-verify citations")}</strong>
                        <p>{t("onboarding.feature3Desc", "Every answer cites the exact sentence on the original page")}</p>
                    </div>
                </div>
            </div>

            <div className={styles.sampleSection}>
                <h3 className={styles.sampleTitle}>
                    {t("onboarding.trySamplesTitle", "Try it now")}
                </h3>
                <p className={styles.sampleDescription}>
                    {t(
                        "onboarding.trySamplesDescription",
                        "Load 3 sample documents — a service agreement, an invoice, and a data policy — then try asking questions across them."
                    )}
                </p>
                {sampleStatus === "idle" && (
                    <Button appearance="outline" size="medium" icon={<DocumentCopy24Regular />} onClick={handleLoadSamples}>
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
                        <span>{t("onboarding.samplesReady", "Sample documents ready! Select \"Sample Documents\" from the folder dropdown in Chat.")}</span>
                    </div>
                )}
                {sampleStatus === "error" && (
                    <div className={styles.sampleError}>
                        <p>{sampleError}</p>
                        <Button appearance="outline" size="small" onClick={handleLoadSamples}>
                            {t("onboarding.retryLoad", "Try again")}
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );

    const renderStep1 = () => (
        <div className={styles.stepContent}>
            <div className={styles.stepHero}>
                <h2 className={styles.stepHeading}>
                    {t("onboarding.step1Title", "Upload your documents")}
                </h2>
                <p className={styles.stepSubheading}>
                    {t("onboarding.step1Description", "Go to Files and upload your PDFs, Word documents, spreadsheets, or images. Evidoc supports 15+ formats. Organize them in folders to query related documents together.")}
                </p>
            </div>

            <div className={styles.tipsList}>
                <div className={styles.tipItem}>
                    <span className={styles.tipEmoji}>📂</span>
                    <p>{t("onboarding.tip1", "Group related documents (contract + invoices) in the same folder for cross-document Q&A")}</p>
                </div>
                <div className={styles.tipItem}>
                    <span className={styles.tipEmoji}>🌍</span>
                    <p>{t("onboarding.tip4", "Ask in any of 13 languages — Evidoc auto-detects and responds in your language")}</p>
                </div>
            </div>

            <Button appearance="primary" size="large" icon={<ArrowUpload24Regular />} onClick={handleGoToFiles}>
                {t("onboarding.uploadFirst", "Upload your first document")}
            </Button>
        </div>
    );

    const renderStep2 = () => (
        <div className={styles.stepContent}>
            <div className={styles.stepHero}>
                <h2 className={styles.stepHeading}>
                    {t("onboarding.step2Title", "Ask a question")}
                </h2>
                <p className={styles.stepSubheading}>
                    {t("onboarding.step2Description", "Go to Chat, select a folder, and type your question in natural language. Evidoc searches across all documents in the folder using a Knowledge Graph — not just keywords.")}
                </p>
            </div>

            <div className={styles.verifyBlock}>
                <h3 className={styles.verifyTitle}>
                    {t("onboarding.step3Title", "Click to verify")}
                </h3>
                <p className={styles.verifyDescription}>
                    {t("onboarding.step3Description", "Every answer includes numbered citations. Click any citation to see the exact sentence highlighted on the original PDF. Verify in seconds — no more manual cross-referencing.")}
                </p>
            </div>

            <div className={styles.tipsList}>
                <div className={styles.tipItem}>
                    <span className={styles.tipEmoji}>🎯</span>
                    <p>{t("onboarding.tip2", "Be specific: \"What is the penalty for late delivery under section 5?\" works better than \"Tell me about penalties\"")}</p>
                </div>
                <div className={styles.tipItem}>
                    <span className={styles.tipEmoji}>⚖️</span>
                    <p>{t("onboarding.tip3", "Try comparison questions: \"Do the invoice amounts match the agreed contract rates?\"")}</p>
                </div>
            </div>

            <Button appearance="primary" size="large" icon={<Chat24Regular />} onClick={handleFinish}>
                {t("onboarding.startChatting", "Start chatting")}
            </Button>
        </div>
    );

    const stepRenderers = [renderStep0, renderStep1, renderStep2];

    return (
        <div className={styles.container}>
            <Helmet>
                <title>{t("onboarding.pageTitle", "Getting Started")} | Evidoc</title>
            </Helmet>

            {/* ── Stepper tabs ── */}
            <div className={styles.stepper}>
                {stepMeta.map((step, i) => (
                    <button
                        key={i}
                        className={`${styles.stepTab} ${i === activeStep ? styles.stepTabActive : ""} ${i < activeStep ? styles.stepTabDone : ""}`}
                        onClick={() => setActiveStep(i)}
                        aria-current={i === activeStep ? "step" : undefined}
                    >
                        <span className={styles.stepTabNumber}>{i < activeStep ? "✓" : i + 1}</span>
                        <span className={styles.stepTabLabel}>{step.label}</span>
                    </button>
                ))}
                <div className={styles.stepperProgress} style={{ width: `${((activeStep) / (STEP_COUNT - 1)) * 100}%` }} />
            </div>

            {/* ── Active step content ── */}
            <div className={styles.stepPanel}>
                {stepRenderers[activeStep]()}
            </div>

            {/* ── Navigation ── */}
            <div className={styles.navBar}>
                {activeStep > 0 ? (
                    <Button appearance="subtle" icon={<ArrowLeft16Regular />} onClick={() => setActiveStep(s => s - 1)}>
                        {t("onboarding.back", "Back")}
                    </Button>
                ) : (
                    <span />
                )}

                <div className={styles.navRight}>
                    <Button appearance="subtle" onClick={handleFinish}>
                        {t("onboarding.skipToChat", "Skip")}
                    </Button>
                    {activeStep < STEP_COUNT - 1 && (
                        <Button appearance="primary" icon={<ArrowRight16Regular />} iconPosition="after" onClick={() => setActiveStep(s => s + 1)}>
                            {t("onboarding.next", "Next")}
                        </Button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default GettingStarted;
