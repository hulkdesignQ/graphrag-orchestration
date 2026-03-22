export const languages = {
  en: { name: "English", flag: "🇬🇧" },
  es: { name: "Español", flag: "🇪🇸" },
  fr: { name: "Français", flag: "🇫🇷" },
  de: { name: "Deutsch", flag: "🇩🇪" },
  ja: { name: "日本語", flag: "🇯🇵" },
  ko: { name: "한국어", flag: "🇰🇷" },
  "zh-cn": { name: "简体中文", flag: "🇨🇳" },
  "zh-tw": { name: "繁體中文", flag: "🇹🇼" },
  nl: { name: "Nederlands", flag: "🇳🇱" },
  da: { name: "Dansk", flag: "🇩🇰" },
  pl: { name: "Polski", flag: "🇵🇱" },
  pt: { name: "Português", flag: "🇵🇹" },
  th: { name: "ไทย", flag: "🇹🇭" },
} as const;

export type Lang = keyof typeof languages;
export const defaultLang: Lang = "en";
