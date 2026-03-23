import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { Helmet } from "react-helmet-async";
import { Button, Spinner } from "@fluentui/react-components";
import {
    ArrowRight16Regular,
    ArrowLeft16Regular,
    DocumentCopy24Regular,
    CheckmarkCircle24Regular,
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

    const finish = () => { markOnboardingSeen(); navigate("/"); };
    const goFiles = () => { markOnboardingSeen(); navigate("/files"); };
    const next = () => setActiveStep(s => Math.min(s + 1, STEP_COUNT - 1));
    const back = () => setActiveStep(s => Math.max(s - 1, 0));

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
            setSampleError(err instanceof Error ? err.message : "Failed to load samples");
        }
    };

    const tabs = [
        t("onboarding.tabUpload", "Upload"),
        t("onboarding.tabAsk", "Ask"),
        t("onboarding.tabVerify", "Verify"),
    ];

    return (
        <div className={styles.container}>
            <Helmet>
                <title>{t("onboarding.pageTitle", "Getting Started")} | Evidoc</title>
            </Helmet>

            {/* ── Stepper ── */}
            <div className={styles.stepper}>
                {tabs.map((label, i) => (
                    <button
                        key={i}
                        className={`${styles.tab} ${i === activeStep ? styles.tabActive : ""} ${i < activeStep ? styles.tabDone : ""}`}
                        onClick={() => setActiveStep(i)}
                    >
                        <span className={styles.tabNumber}>{i < activeStep ? "✓" : i + 1}</span>
                        <span className={styles.tabLabel}>{label}</span>
                    </button>
                ))}
                <div className={styles.progress} style={{ width: `${(activeStep / (STEP_COUNT - 1)) * 100}%` }} />
            </div>

            {/* ── Step content ── */}
            <div className={styles.panel} key={activeStep}>
                {activeStep === 0 && (
                    <>
                        <div className={styles.illustration}>📄</div>
                        <h1 className={styles.heading}>{t("onboarding.uploadHeading", "Upload your documents")}</h1>
                        <p className={styles.body}>{t("onboarding.uploadBody", "Drop PDFs, Word docs, Excel, or images into a folder. We'll build a Knowledge Graph so you can search across them.")}</p>
                        <div className={styles.actions}>
                            <Button appearance="primary" size="large" onClick={goFiles}>{t("onboarding.uploadCta", "Go to Files")}</Button>
                            <Button appearance="subtle" size="medium" onClick={next}>{t("onboarding.or", "or continue the tour →")}</Button>
                        </div>
                        <div className={styles.divider} />
                        <p className={styles.hint}>{t("onboarding.sampleHint", "No documents yet? Try our samples:")}</p>
                        {sampleStatus === "idle" && (
                            <Button appearance="outline" size="small" icon={<DocumentCopy24Regular />} onClick={handleLoadSamples}>
                                {t("onboarding.loadSamples", "Load sample documents")}
                            </Button>
                        )}
                        {sampleStatus === "loading" && <div className={styles.sampleLoading}><Spinner size="tiny" /><span>{t("onboarding.loadingSamples", "Loading...")}</span></div>}
                        {sampleStatus === "done" && <div className={styles.sampleDone}><CheckmarkCircle24Regular /><span>{t("onboarding.samplesReady", "Samples loaded!")}</span></div>}
                        {sampleStatus === "error" && <div className={styles.sampleError}><span>{sampleError}</span> <Button appearance="subtle" size="small" onClick={handleLoadSamples}>{t("onboarding.retryLoad", "Retry")}</Button></div>}
                    </>
                )}

                {activeStep === 1 && (
                    <>
                        <div className={styles.illustration}>💬</div>
                        <h1 className={styles.heading}>{t("onboarding.askHeading", "Ask a question")}</h1>
                        <p className={styles.body}>{t("onboarding.askBody", "Pick a folder, type your question. Evidoc searches across all documents using a Knowledge Graph — not just keywords.")}</p>
                    </>
                )}

                {activeStep === 2 && (
                    <>
                        <div className={styles.illustration}>✅</div>
                        <h1 className={styles.heading}>{t("onboarding.verifyHeading", "Click to verify")}</h1>
                        <p className={styles.body}>{t("onboarding.verifyBody", "Every answer has numbered citations. Click one to jump to the exact sentence on the original page.")}</p>
                        <Button appearance="primary" size="large" onClick={finish}>{t("onboarding.startChatting", "Start chatting")}</Button>
                    </>
                )}
            </div>

            {/* ── Nav ── */}
            <div className={styles.nav}>
                {activeStep > 0 ? (
                    <Button appearance="subtle" icon={<ArrowLeft16Regular />} onClick={back}>{t("onboarding.back", "Back")}</Button>
                ) : <span />}
                <div className={styles.navRight}>
                    <Button appearance="subtle" onClick={finish}>{t("onboarding.skip", "Skip")}</Button>
                    {activeStep < STEP_COUNT - 1 && (
                        <Button appearance="primary" icon={<ArrowRight16Regular />} iconPosition="after" onClick={next}>{t("onboarding.next", "Next")}</Button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default GettingStarted;
