import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { DEFAULT_LANGUAGE, normalizeLanguageCode } from "./constants/languages";
import en from "./locales/en.json";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
  },
  lng: DEFAULT_LANGUAGE,
  fallbackLng: DEFAULT_LANGUAGE,
  interpolation: {
    escapeValue: false,
  },
});

export async function loadLanguage(lang: string): Promise<void> {
  const normalizedLanguage = normalizeLanguageCode(lang);

  if (normalizedLanguage === DEFAULT_LANGUAGE) return;
  if (i18n.hasResourceBundle(normalizedLanguage, "translation")) return;

  const messages = await import(`./locales/${normalizedLanguage}.json`);
  i18n.addResourceBundle(normalizedLanguage, "translation", messages.default);
}

export default i18n;
