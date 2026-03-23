import { useEffect, useCallback, useState, useContext } from "react";
import { Link, useLocation } from "react-router-dom";
import { useMsal } from "@azure/msal-react";
import { useTranslation } from "react-i18next";
import styles from "./Dashboard.module.css";
import { useLogin, getToken, isUsingAppServicesLogin } from "../../authConfig";
import { LoginContext } from "../../loginContext";
import { fetchDashboardAll, UserProfileResponse, UsageStats, PlanInfo } from "../../api/dashboard";
import { fetchBillingConfig, fetchSubscription, createCheckoutSession, createPortalSession, BillingConfig, SubscriptionStatus } from "../../api/billing";
import { Events } from "../../analytics";

const PLAN_BADGE_CLASS: Record<string, string> = {
    free: styles.planFree,
    pro: styles.planPro,
    pro_plus: styles.planProPlus,
    enterprise: styles.planEnterprise
};

const PLAN_FEATURES: Record<string, string[]> = {
    free: ["planFeature.free.f1", "planFeature.free.f2", "planFeature.free.f3", "planFeature.free.f4"],
    pro: ["planFeature.pro.f1", "planFeature.pro.f2", "planFeature.pro.f3", "planFeature.pro.f4", "planFeature.pro.f5"],
    pro_plus: ["planFeature.pro_plus.f1", "planFeature.pro_plus.f2", "planFeature.pro_plus.f3", "planFeature.pro_plus.f4", "planFeature.pro_plus.f5"],
    business: ["planFeature.business.f1", "planFeature.business.f2", "planFeature.business.f3", "planFeature.business.f4", "planFeature.business.f5", "planFeature.business.f6"],
    enterprise: ["planFeature.enterprise.f1", "planFeature.enterprise.f2", "planFeature.enterprise.f3", "planFeature.enterprise.f4", "planFeature.enterprise.f5", "planFeature.enterprise.f6"]
};

const HIGHLIGHTED_PLANS = new Set(["pro_plus", "enterprise"]);
const BADGE_PLANS: Record<string, string> = { pro_plus: "planBadge.popular", enterprise: "planBadge.custom" };

function formatStorage(gb: number): string {
    if (gb <= 0) return "0 MB";
    if (gb < 0.1) return `${(gb * 1024).toFixed(1)} MB`;
    return `${gb.toFixed(1)} GB`;
}

function usePct(used: number, limit: number): { pct: number; color: string } {
    if (limit <= 0) return { pct: 0, color: styles.barGreen };
    const pct = Math.min(100, Math.round((used / limit) * 100));
    const color = pct > 90 ? styles.barRed : pct > 70 ? styles.barYellow : styles.barGreen;
    return { pct, color };
}

const Dashboard = () => {
    const { loggedIn } = useContext(LoginContext);
    const { t } = useTranslation();
    const client = useLogin ? useMsal().instance : undefined;

    const [profile, setProfile] = useState<UserProfileResponse | null>(null);
    const [usage, setUsage] = useState<UsageStats | null>(null);
    const [plans, setPlans] = useState<PlanInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [sessionExpired, setSessionExpired] = useState(false);
    const [billingConfig, setBillingConfig] = useState<BillingConfig | null>(null);
    const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
    const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
    const [billingMessage, setBillingMessage] = useState<{ type: "success" | "cancel" | "error"; text: string } | null>(null);

    // All tiers support self-service Stripe checkout

    // Handle ?billing=success / ?billing=cancel from Stripe redirect
    const location = useLocation();
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const billingParam = params.get("billing");
        if (billingParam === "success") {
            setBillingMessage({ type: "success", text: t("dashboard.billingSuccess") });
            // Clean URL without reload
            window.history.replaceState({}, "", location.pathname + location.hash);
        } else if (billingParam === "cancel") {
            setBillingMessage({ type: "cancel", text: t("dashboard.billingCancelled") });
            window.history.replaceState({}, "", location.pathname + location.hash);
        }
    }, [location.search, t]);

    const handleReLogin = () => {
        if (isUsingAppServicesLogin) {
            window.location.href = ".auth/login/aad?post_login_redirect_uri=" + encodeURIComponent(window.location.pathname + window.location.search);
        } else {
            // MSAL: clear cache and reload to trigger interactive login
            client?.logoutRedirect({ postLogoutRedirectUri: window.location.pathname });
        }
    };

    const loadDashboard = useCallback(async () => {
        try {
            const token = client ? await getToken(client) : undefined;
            const [data, billing] = await Promise.all([
                fetchDashboardAll(token),
                fetchBillingConfig(),
            ]);
            setProfile(data.profile);
            setUsage(data.usage);
            setPlans(data.plans);
            setBillingConfig(billing);

            // Fetch subscription details if Stripe is enabled
            if (billing.stripe_enabled) {
                const sub = await fetchSubscription(token);
                setSubscription(sub);
            }
        } catch (e: any) {
            const msg = e.message || "Failed to load dashboard";
            if (msg.includes("401") || msg.toLowerCase().includes("expired") || msg.toLowerCase().includes("unauthorized")) {
                setSessionExpired(true);
            } else {
                setError(msg);
            }
        } finally {
            setLoading(false);
        }
    }, [client]);

    useEffect(() => {
        if (!loggedIn) {
            setLoading(false);
            return;
        }

        loadDashboard();
        Events.dashboardViewed();

        // Re-fetch when user returns to this tab (e.g. after making queries)
        const handleVisibility = () => {
            if (document.visibilityState === "visible") {
                loadDashboard();
            }
        };
        document.addEventListener("visibilitychange", handleVisibility);
        return () => document.removeEventListener("visibilitychange", handleVisibility);
    }, [loggedIn, loadDashboard]);

    // --- Login required ---
    if (!loggedIn) {
        return (
            <div className={styles.loginRequired}>
                <span>🔒</span>
                <h2>{t("dashboard.signInRequired")}</h2>
                <p>{t("dashboard.signInToView")}</p>
            </div>
        );
    }

    // --- Loading ---
    if (loading) {
        return (
            <div className={styles.loadingContainer}>
                <div className={styles.spinner} />
            </div>
        );
    }

    // --- Session expired ---
    if (sessionExpired) {
        return (
            <div className={styles.loginRequired}>
                <span>🔑</span>
                <h2>{t("dashboard.sessionExpired")}</h2>
                <p>{t("dashboard.sessionExpiredMessage")}</p>
                <button className={styles.upgradeButton} onClick={handleReLogin}>
                    {t("dashboard.signIn")}
                </button>
            </div>
        );
    }

    // --- Error ---
    if (error) {
        return (
            <div className={styles.errorContainer}>
                <span>⚠️</span>
                <p>{error}</p>
            </div>
        );
    }

    if (!profile || !usage) return null;

    const queryMonth = usePct(usage.queries_this_month, usage.queries_limit_month);
    const credits = usePct(usage.credits_used_month, usage.credits_limit_month ?? 0);
    const storage = usePct(usage.storage_used_gb, usage.storage_limit_gb);

    return (
        <div className={styles.dashboardContainer}>
            {/* Header */}
            <div className={styles.dashboardHeader}>
                <div>
                    <h1 className={styles.greeting}>
                        {profile.display_name ? t("dashboard.hello", { name: profile.display_name }) : t("dashboard.title")}
                    </h1>
                    {profile.email && (
                        <span className={styles.statSubtext}>{profile.email}</span>
                    )}
                </div>
                <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    <span className={`${styles.planBadge} ${PLAN_BADGE_CLASS[profile.plan] || styles.planFree}`}>
                        {profile.plan}
                    </span>
                    {profile.is_admin && (
                        <Link to="/admin" className={styles.adminLink}>
                            ⚙️ {t("dashboard.adminDashboard")}
                        </Link>
                    )}
                </div>
            </div>

            {/* Stats */}
            {usage.data_degraded && (
                <div className={styles.degradedBanner}>
                    ⚠️ {t("dashboard.dataDegraded")}
                </div>
            )}
            {billingMessage && (
                <div className={`${styles.billingBanner} ${styles[`billing${billingMessage.type.charAt(0).toUpperCase() + billingMessage.type.slice(1)}`]}`}>
                    <span>{billingMessage.type === "success" ? "✅" : billingMessage.type === "error" ? "⚠️" : "ℹ️"} {billingMessage.text}</span>
                    <button className={styles.billingBannerClose} onClick={() => setBillingMessage(null)}>✕</button>
                </div>
            )}
            <div className={styles.statsGrid}>
                <div className={styles.statCard}>
                    <span className={styles.statLabel}>{t("dashboard.queriesThisMonth")}</span>
                    <span className={styles.statValue}>{usage.queries_this_month}</span>
                    <span className={styles.statSubtext}>{t("dashboard.monthlyLimit", { limit: usage.queries_limit_month })}</span>
                    <div className={styles.statBar}>
                        <div className={`${styles.statBarFill} ${queryMonth.color}`} style={{ width: `${queryMonth.pct}%` }} />
                    </div>
                </div>

                <div className={styles.statCard}>
                    <span className={styles.statLabel}>{t("dashboard.creditsUsed")}</span>
                    <span className={styles.statValue}>{usage.credits_used_month.toLocaleString()}</span>
                    <span className={styles.statSubtext}>
                        {usage.credits_limit_month != null ? t("dashboard.monthlyCredits", { limit: usage.credits_limit_month.toLocaleString() }) : t("dashboard.unlimitedCredits")}
                        {usage.translated_queries_month > 0 && ` · ${t("dashboard.translated", { count: usage.translated_queries_month })}`}
                        {usage.speech_queries_month > 0 && ` · ${t("dashboard.voice", { count: usage.speech_queries_month })}`}
                    </span>
                    <div className={styles.statBar}>
                        <div className={`${styles.statBarFill} ${credits.color}`} style={{ width: `${credits.pct}%` }} />
                    </div>
                </div>

                <div className={styles.statCard}>
                    <span className={styles.statLabel}>{t("dashboard.documents")}</span>
                    <span className={styles.statValue}>{usage.documents_count}</span>
                </div>

                <div className={styles.statCard}>
                    <span className={styles.statLabel}>{t("dashboard.storageUsed")}</span>
                    <span className={styles.statValue}>{formatStorage(usage.storage_used_gb)}</span>
                    <span className={styles.statSubtext}>{t("dashboard.gbLimit", { limit: usage.storage_limit_gb })}</span>
                    <div className={styles.statBar}>
                        <div className={`${styles.statBarFill} ${storage.color}`} style={{ width: `${storage.pct}%` }} />
                    </div>
                </div>
            </div>

            {/* Recent Activity */}
            {usage.recent_queries.length > 0 && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>{t("dashboard.recentActivity")}</h2>
                    <table className={styles.recentTable}>
                        <thead>
                            <tr>
                                <th>{t("dashboard.time")}</th>
                                <th>{t("dashboard.tokens")}</th>
                                <th>{t("dashboard.credits")}</th>
                                <th>{t("dashboard.language")}</th>
                            </tr>
                        </thead>
                        <tbody>
                            {usage.recent_queries.slice(0, 10).map((q, i) => (
                                <tr key={i}>
                                    <td>{q.timestamp ? new Date(q.timestamp).toLocaleString() : "—"}</td>
                                    <td>{q.total_tokens ?? "—"}</td>
                                    <td>{q.credits_used ?? "—"}</td>
                                    <td>
                                        {q.detected_language || q.speech_detected_language
                                            ? `${q.was_speech_input ? "🎤 " : ""}${(q.speech_detected_language || q.detected_language || "").toUpperCase()}${q.was_translated ? " 🌐" : ""}`
                                            : "—"}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Plans comparison */}
            {plans && (
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>{t("dashboard.plans")}</h2>
                    <div className={styles.planGrid}>
                        {Object.entries(plans.plans).map(([tier, info]) => {
                            const isCurrent = tier === plans.current_plan;
                            const canCheckout = billingConfig?.stripe_enabled && tier !== "free";
                            const isUpgrade = !isCurrent && canCheckout;
                            const isHighlighted = HIGHLIGHTED_PLANS.has(tier);
                            const badgeKey = BADGE_PLANS[tier];
                            const isBusinessTier = tier === "business" || tier === "enterprise";
                            const periodKey = isBusinessTier ? "dashboard.planPeriod.business" : "dashboard.planPeriod.individual";
                            const features = PLAN_FEATURES[tier] || [];
                            return (
                                <div
                                    key={tier}
                                    className={`${styles.planCard} ${isCurrent ? styles.planCardCurrent : ""} ${isHighlighted ? styles.planCardHighlighted : ""}`}
                                >
                                    {badgeKey && (
                                        <span className={styles.planCardBadge}>{t(`dashboard.${badgeKey}`)}</span>
                                    )}
                                    <div className={`${styles.planCardName} ${isHighlighted ? styles.planCardNameHighlighted : ""}`}>
                                        {info.name}
                                    </div>
                                    <div className={styles.planCardPrice}>
                                        {t(`dashboard.planPrice.${tier}`)}
                                        {tier !== "free" && (
                                            <span className={styles.planCardPeriod}>{t(`dashboard.${periodKey.replace("dashboard.", "")}`)}</span>
                                        )}
                                    </div>
                                    <p className={styles.planCardDesc}>{t(`dashboard.planDesc.${tier}`)}</p>
                                    <ul className={styles.planCardFeatures}>
                                        {features.map((fKey) => (
                                            <li key={fKey}>{t(`dashboard.${fKey}`)}</li>
                                        ))}
                                    </ul>
                                    {info.advanced_analytics && <p className={styles.planCardDetail}>✅ {t("dashboard.featureAdvancedAnalytics")}</p>}
                                    {info.api_access && <p className={styles.planCardDetail}>✅ {t("dashboard.featureApiAccess")}</p>}
                                    <button
                                        className={`${styles.upgradeButton} ${tier === "free" && !isCurrent ? styles.upgradeButtonOutline : ""}`}
                                        disabled={isCurrent || checkoutLoading === tier || (!isCurrent && !isUpgrade && tier !== "free")}
                                        onClick={async () => {
                                            if (isCurrent) return;
                                            Events.planUpgradeClicked({ currentPlan: plans.current_plan, targetPlan: tier });
                                            if (isUpgrade) {
                                                try {
                                                    setCheckoutLoading(tier);
                                                    setBillingMessage(null);
                                                    const token = client ? await getToken(client) : undefined;
                                                    const { checkout_url } = await createCheckoutSession(tier, token);
                                                    window.location.href = checkout_url;
                                                } catch (err: any) {
                                                    setBillingMessage({ type: "error", text: err.message || "Failed to start checkout" });
                                                    setCheckoutLoading(null);
                                                }
                                            }
                                        }}
                                    >
                                        {isCurrent
                                            ? t("dashboard.currentPlan")
                                            : checkoutLoading === tier
                                                ? "..."
                                                : !canCheckout && tier !== "free"
                                                    ? t("dashboard.contactSales")
                                                    : tier === "free"
                                                        ? t("dashboard.planCta.getStarted")
                                                        : t("dashboard.planCta.upgradeTo", { plan: info.name })}
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                    {/* Subscription status & Manage Billing */}
                    {billingConfig?.stripe_enabled && profile.plan !== "free" && (
                        <div className={styles.subscriptionStatus}>
                            {subscription?.has_subscription && (
                                <>
                                    {subscription.cancel_at_period_end && (
                                        <p className={styles.cancelNotice}>
                                            ⚠️ {t("dashboard.cancelAtPeriodEnd", {
                                                date: subscription.current_period_end
                                                    ? new Date(subscription.current_period_end).toLocaleDateString()
                                                    : "—"
                                            })}
                                        </p>
                                    )}
                                    {subscription.current_period_end && !subscription.cancel_at_period_end && (
                                        <p className={styles.renewalInfo}>
                                            {t("dashboard.nextRenewal", {
                                                date: new Date(subscription.current_period_end).toLocaleDateString()
                                            })}
                                        </p>
                                    )}
                                </>
                            )}
                            <button
                                className={styles.upgradeButton}
                                style={{ marginTop: "0.5rem" }}
                                onClick={async () => {
                                    try {
                                        const token = client ? await getToken(client) : undefined;
                                        const { portal_url } = await createPortalSession(token);
                                        window.location.href = portal_url;
                                    } catch (err: any) {
                                        setBillingMessage({ type: "error", text: err.message || "Failed to open billing portal" });
                                    }
                                }}
                            >
                                💳 {t("dashboard.manageBilling")}
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default Dashboard;
