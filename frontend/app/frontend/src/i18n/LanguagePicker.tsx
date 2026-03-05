import { useTranslation } from "react-i18next";
import { LocalLanguage24Regular, LocalLanguage20Regular } from "@fluentui/react-icons";
import { Dropdown, Option, OptionOnSelectData, SelectionEvents } from "@fluentui/react-components";
import { useId } from "react";

import { supportedLngs } from "./config";
import styles from "./LanguagePicker.module.css";

interface Props {
    onLanguageChange: (language: string) => void;
    variant?: "default" | "header";
}

export const LanguagePicker = ({ onLanguageChange, variant = "default" }: Props) => {
    const { i18n } = useTranslation();

    const handleLanguageChange = (_ev: SelectionEvents, data: OptionOnSelectData) => {
        onLanguageChange(data.optionValue || i18n.language);
    };
    const languagePickerId = useId();
    const { t } = useTranslation();

    const isHeader = variant === "header";

    return (
        <div className={isHeader ? styles.languagePickerHeader : styles.languagePicker}>
            {isHeader ? (
                <LocalLanguage20Regular className={styles.languagePickerIconHeader} />
            ) : (
                <LocalLanguage24Regular className={styles.languagePickerIcon} />
            )}
            <Dropdown
                id={languagePickerId}
                selectedOptions={[i18n.language]}
                value={supportedLngs[i18n.language]?.name || i18n.language}
                onOptionSelect={handleLanguageChange}
                aria-label={t("labels.languagePicker")}
                appearance="underline"
                size={isHeader ? "small" : "medium"}
                className={isHeader ? styles.languagePickerDropdownHeader : undefined}
            >
                {Object.entries(supportedLngs).map(([code, details]) => (
                    <Option key={code} value={code}>
                        {details.name}
                    </Option>
                ))}
            </Dropdown>
        </div>
    );
};
