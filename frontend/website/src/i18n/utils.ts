import { defaultLang, type Lang } from "./languages";
import { ui } from "./ui";

export function useTranslations(lang: Lang | string | undefined) {
  const l = (lang ?? defaultLang) as Lang;
  return function t(key: keyof (typeof ui)[typeof defaultLang]): string {
    return (ui[l] as Record<string, string>)?.[key] ?? ui[defaultLang][key] ?? key;
  };
}

export function getLocalePath(lang: Lang | string, path: string = "/") {
  if (lang === defaultLang) return path;
  return `/${lang}${path}`;
}
