import { Outlet, NavLink } from "react-router-dom";
import { useState, useEffect, useCallback, useContext } from "react";
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
import { hasSeenOnboarding } from "../../utils/onboarding";
import appLogo from "../../assets/applogo.png";

const NAV_ICONS: Array<{ to: string; end?: boolean; icon: React.ReactNode; labelKey: string; step: number }> = [
    { to: "/", end: true, icon: <Chat24Regular />, labelKey: "nav.chat", step: 2 },
    { to: "/files", icon: <Folder24Regular />, labelKey: "nav.files", step: 1 },
    { to: "/dashboard", icon: <Board24Regular />, labelKey: "nav.dashboard", step: 0 },
];

const Layout = () => {
    const { t, i18n } = useTranslation();
    const { loggedIn } = useContext(LoginContext);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [showLanguagePicker, setShowLanguagePicker] = useState(false);
    const [showOnboarding, setShowOnboarding] = useState(false);

    useEffect(() => {
        configApi().then(config => setShowLanguagePicker(config.showLanguagePicker));
    }, []);

    useEffect(() => {
        if (loggedIn && !hasSeenOnboarding()) {
            setShowOnboarding(true);
        }
    }, [loggedIn]);

    const toggleSidebar = useCallback(() => setSidebarOpen(prev => !prev), []);
    const closeSidebar = useCallback(() => setSidebarOpen(false), []);

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
                        {NAV_ICONS.map(({ to, end, icon, labelKey, step }) => (
                            <NavLink
                                key={to}
                                to={to}
                                end={end}
                                className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ""}`}
                                onClick={closeSidebar}
                            >
                                <span className={styles.navIcon}>
                                    {icon}
                                    {showOnboarding && step > 0 && (
                                        <span className={styles.onboardingBadge}>{step}</span>
                                    )}
                                </span>
                                <span className={styles.navLabel}>{t(labelKey)}</span>
                                {showOnboarding && step > 0 && (
                                    <span className={styles.onboardingHint}>
                                        {t(`onboarding.step${step}`)}
                                    </span>
                                )}
                            </NavLink>
                        ))}

                        {/* Bottom spacer pushes version to bottom */}
                        <div className={styles.navSpacer} />
                        {showOnboarding && (
                            <button className={styles.onboardingDismiss} onClick={() => { setShowOnboarding(false); import("../../utils/onboarding").then(m => m.markOnboardingSeen()); }}>
                                {t("onboarding.dismiss", "Got it")}
                            </button>
                        )}
                        <div className={styles.navVersion}>v2.0</div>
                    </nav>
                )}

                {/* Main content area */}
                <main className={styles.main} id="main-content">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default Layout;
