import { useCases, useCaseOrder, type UseCase } from "./use-cases";
import type { Lang } from "../i18n/languages";

import { useCasesEs } from "./locales/use-cases-es";
import { useCasesFr } from "./locales/use-cases-fr";
import { useCasesDe } from "./locales/use-cases-de";
import { useCasesJa } from "./locales/use-cases-ja";
import { useCasesKo } from "./locales/use-cases-ko";
import { useCasesZhCn } from "./locales/use-cases-zh-cn";
import { useCasesZhTw } from "./locales/use-cases-zh-tw";
import { useCasesNl } from "./locales/use-cases-nl";
import { useCasesDa } from "./locales/use-cases-da";
import { useCasesPl } from "./locales/use-cases-pl";
import { useCasesPt } from "./locales/use-cases-pt";
import { useCasesTh } from "./locales/use-cases-th";

const allUseCases: Record<string, Record<string, UseCase>> = {
  en: useCases,
  es: useCasesEs,
  fr: useCasesFr,
  de: useCasesDe,
  ja: useCasesJa,
  ko: useCasesKo,
  "zh-cn": useCasesZhCn,
  "zh-tw": useCasesZhTw,
  nl: useCasesNl,
  da: useCasesDa,
  pl: useCasesPl,
  pt: useCasesPt,
  th: useCasesTh,
};

export function getLocalizedUseCases(lang: Lang | string): Record<string, UseCase> {
  return allUseCases[lang] || useCases;
}

export { useCaseOrder };
