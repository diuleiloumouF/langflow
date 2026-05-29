export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English" },
  { code: "fr", label: "Français" },
  { code: "es", label: "Español" },
  { code: "de", label: "Deutsch" },
  { code: "pt", label: "Português" },
  { code: "ja", label: "日本語" },
  { code: "zh-Hans", label: "中文" },
] as const;

export const DEFAULT_LANGUAGE = "en";

export type SupportedLanguageCode =
  (typeof SUPPORTED_LANGUAGES)[number]["code"];

const SUPPORTED_LANGUAGE_CODES = new Set<string>(
  SUPPORTED_LANGUAGES.map((language) => language.code),
);

const LANGUAGE_ALIASES: Record<string, SupportedLanguageCode> = {
  zh: "zh-Hans",
  "zh-cn": "zh-Hans",
  "zh-hans": "zh-Hans",
  "zh-sg": "zh-Hans",
};

export function normalizeLanguageCode(
  language?: string | null,
): SupportedLanguageCode {
  if (!language) {
    return DEFAULT_LANGUAGE;
  }

  if (SUPPORTED_LANGUAGE_CODES.has(language)) {
    return language as SupportedLanguageCode;
  }

  const normalizedLanguage = language.toLowerCase();
  const aliasedLanguage = LANGUAGE_ALIASES[normalizedLanguage];

  if (aliasedLanguage) {
    return aliasedLanguage;
  }

  const baseLanguage = normalizedLanguage.split("-")[0];
  if (SUPPORTED_LANGUAGE_CODES.has(baseLanguage)) {
    return baseLanguage as SupportedLanguageCode;
  }

  return DEFAULT_LANGUAGE;
}
