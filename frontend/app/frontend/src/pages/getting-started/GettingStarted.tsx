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

    const steps = [
        {
            num: "1",
            title: t("onboarding.step1Title", "Drop Your Files"),
            desc: t("onboarding.step1Desc", "PDFs, Word docs, spreadsheets, scanned images — 15+ formats. Drag, drop, done."),
        },
        {
            num: "2",
            title: t("onboarding.step2Title", "Evidoc Connects the Dots"),
            desc: t("onboarding.step2Desc", "Every name, date, clause, and concept is linked across all your documents."),
        },
        {
            num: "3",
            title: t("onboarding.step3Title", "Ask. Verify. Done."),
            desc: t("onboarding.step3Desc", "Ask in plain English (or 12 other languages). Click any citation to see the highlighted source."),
        },
    ];

    return (
        <div className={styles.container}>
            <Helmet>
                <title>{t("onboarding.pageTitle", "Getting Started")} | Evidoc</title>
            </Helmet>

            {/* ── Heading ── */}
            <h1 className={styles.headline}>{t("onboarding.headline", "Three steps. That's it.")}</h1>
            <p className={styles.subheadline}>{t("onboarding.subheadline", "From \"I have 200 PDFs\" to \"here's the exact answer, with proof.\"")}</p>

            {/* ── Steps grid (matches website HowItWorks) ── */}
            <div className={styles.stepsGrid}>
                {steps.map((step) => (
                    <div key={step.num} className={`${styles.stepCard} ${activeStep === Number(step.num) - 1 ? styles.stepCardActive : ""}`} onClick={() => setActiveStep(Number(step.num) - 1)}>
                        <div className={styles.stepCircle}>{step.num}</div>
                        <h3 className={styles.stepTitle}>{step.title}</h3>
                        <p className={styles.stepDesc}>{step.desc}</p>
                    </div>
                ))}
            </div>

            {/* ── CTA area (changes based on active step) ── */}
            <div className={styles.ctaArea} key={activeStep}>
                {activeStep === 0 && (
                    <>
                        <Button appearance="primary" size="large" onClick={goFiles}>{t("onboarding.uploadCta", "Go to Files")}</Button>
                        <div className={styles.sampleRow}>
                            <span className={styles.sampleHint}>{t("onboarding.sampleHint", "No documents yet?")}</span>
                            {sampleStatus === "idle" && (
                                <Button appearance="subtle" size="small" icon={<DocumentCopy24Regular />} onClick={handleLoadSamples}>{t("onboarding.loadSamples", "Load samples")}</Button>
                            )}
                            {sampleStatus === "loading" && <span className={styles.sampleLoading}><Spinner size="tiny" /> {t("onboarding.loadingSamples", "Loading...")}</span>}
                            {sampleStatus === "done" && <span className={styles.sampleDone}><CheckmarkCircle24Regular /> {t("onboarding.samplesReady", "Loaded!")}</span>}
                            {sampleStatus === "error" && <span className={styles.sampleError}>{sampleError} <Button appearance="subtle" size="small" onClick={handleLoadSamples}>{t("onboarding.retryLoad", "Retry")}</Button></span>}
                        </div>
                    </>
                )}
                {activeStep === 1 && (
                    <p className={styles.ctaNote}>{t("onboarding.connectNote", "This happens automatically after you upload — no setup needed.")}</p>
                )}
                {activeStep === 2 && (
                    <Button appearance="primary" size="large" onClick={finish}>{t("onboarding.startChatting", "Start chatting")}</Button>
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
