import { Outlet, NavLink } from "react-router-dom";
import { useState, useEffect, useCallback, useContext, useRef } from "react";
import { useTranslation } from "react-i18next";
import {
    Chat24Regular,
    Folder24Regular,
    Board24Regular,
} from "@fluentui/react-icons";
import styles from "./Layout.module.css";

import { useLogin } from "../../authConfig";
import { LoginButton } from "../../components/LoginButton";
import { LanguagePicker } from "../../i18n/LanguagePicker";
import { LoginContext } from "../../loginContext";
import { configApi } from "../../api";
import { hasSeenOnboarding, markOnboardingSeen } from "../../utils/onboarding";
import appLogo from "../../assets/applogo.png";

const NAV_ICONS: Array<{ to: string; end?: boolean; icon: React.ReactNode; labelKey: string; step: number }> = [
    { to: "/", end: true, icon: <Chat24Regular />, labelKey: "nav.chat", step: 0 },
    { to: "/files", icon: <Folder24Regular />, labelKey: "nav.files", step: 1 },
    { to: "/dashboard", icon: <Board24Regular />, labelKey: "nav.dashboard", step: 2 },
];

// Onboarding tour steps: step number → description key
const TOUR_STEPS = [
    { navStep: 1, labelKey: "onboarding.step1" },
    { navStep: 0, labelKey: "onboarding.step2" },
    { navStep: 2, labelKey: "onboarding.step3" },
];

const Layout = () => {
    const { t, i18n } = useTranslation();
    const { loggedIn } = useContext(LoginContext);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [showLanguagePicker, setShowLanguagePicker] = useState(false);
    const [tourStep, setTourStep] = useState(-1); // -1 = inactive
    const navRefs = useRef<(HTMLAnchorElement | null)[]>([]);

    useEffect(() => {
        configApi().then(config => setShowLanguagePicker(config.showLanguagePicker));
    }, []);

    useEffect(() => {
        if (loggedIn && !hasSeenOnboarding()) {
            setTourStep(0);
        }
    }, [loggedIn]);

    const advanceTour = useCallback(() => {
        setTourStep(prev => {
            const next = prev + 1;
            if (next >= TOUR_STEPS.length) {
                markOnboardingSeen();
                return -1;
            }
            return next;
        });
    }, []);

    const dismissTour = useCallback(() => {
        setTourStep(-1);
        markOnboardingSeen();
    }, []);

    const toggleSidebar = useCallback(() => setSidebarOpen(prev => !prev), []);
    const closeSidebar = useCallback(() => setSidebarOpen(false), []);

    // Find which nav index the current tour step points to
    const activeTourNavStep = tourStep >= 0 ? TOUR_STEPS[tourStep].navStep : -1;

    return (
        <div className={styles.layout}>
            {/* Top header bar */}
            <header className={styles.header} role="banner">
                <div className={styles.headerContainer}>
                    <div className={styles.headerLeft}>
                        {loggedIn && (
                            <button
                                className={styles.menuToggle}
                                onClick={toggleSidebar}
                                aria-label={t("nav.toggleNavigation")}
                                aria-expanded={sidebarOpen}
                            >
                                <span className={styles.hamburger} />
                            </button>
                        )}
                        <NavLink to="/" className={styles.headerTitleContainer} onClick={closeSidebar}>
                            <img src={appLogo} alt="Hulkdesign AI" className={styles.headerLogo} />
                            <h3 className={styles.headerTitle}>{t("headerTitle")}</h3>
                        </NavLink>
                    </div>
                    <div className={styles.headerRight}>
                        {showLanguagePicker && <LanguagePicker onLanguageChange={newLang => i18n.changeLanguage(newLang)} variant="header" />}
                        {useLogin && <LoginButton />}
                    </div>
                </div>
            </header>

            <div className={styles.body}>
                {/* Sidebar overlay for mobile */}
                {sidebarOpen && loggedIn && <div className={styles.sidebarOverlay} onClick={closeSidebar} />}

                {/* Sidebar navigation — only shown after login */}
                {loggedIn && (
                    <nav className={`${styles.sidebar} ${sidebarOpen ? styles.sidebarOpen : ""}`} aria-label="Main navigation">
                        {NAV_ICONS.map(({ to, end, icon, labelKey, step }, idx) => (
                            <NavLink
                                key={to}
                                to={to}
                                end={end}
                                ref={el => { navRefs.current[idx] = el; }}
                                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ""}`}
                                onClick={closeSidebar}
                            >
                                <span className={styles.navIcon}>{icon}</span>
                                <span className={styles.navLabel}>{t(labelKey)}</span>
                                {/* Tour tooltip positioned beside the nav icon */}
                                {step === activeTourNavStep && (
                                    <div className={styles.tourTooltip} onClick={e => { e.preventDefault(); e.stopPropagation(); advanceTour(); }}>
                                        <span className={styles.tourBadge}>{tourStep + 1}</span>
                                        <span className={styles.tourText}>{t(TOUR_STEPS[tourStep].labelKey)}</span>
                                        <span className={styles.tourAction}>
                                            {tourStep < TOUR_STEPS.length - 1 ? t("onboarding.next", "Next →") : t("onboarding.done", "Got it ✓")}
                                        </span>
                                    </div>
                                )}
                            </NavLink>
                        ))}

                        {/* Bottom spacer pushes version to bottom */}
                        <div className={styles.navSpacer} />
                        <div className={styles.navVersion}>v2.0</div>
                    </nav>
                )}

                {/* Tour backdrop overlay */}
                {tourStep >= 0 && <div className={styles.tourOverlay} onClick={dismissTour} />}

                {/* Main content area */}
                <main className={styles.main} id="main-content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default Layout;
