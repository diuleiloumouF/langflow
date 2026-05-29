/**
 * Tests for the loadLanguage lazy-loader in i18n.ts.
 *
 * jest.setup.js mocks react-i18next globally, but this file imports the real
 * i18n instance directly — so those tests are unaffected by the global mock.
 */

// Import the real i18n instance and loadLanguage (not the mock from jest.setup.js)
jest.unmock("react-i18next");

import { DEFAULT_LANGUAGE, normalizeLanguageCode } from "./constants/languages";
import i18n, { loadLanguage } from "./i18n";

describe("loadLanguage", () => {
  beforeEach(() => {
    // Clear cached non-English bundles between tests
    ["fr", "ja", "es", "de", "pt", "zh-Hans"].forEach((lang) => {
      if (i18n.hasResourceBundle(lang, "translation")) {
        i18n.removeResourceBundle(lang, "translation");
      }
    });
  });

  it("does not call addResourceBundle for 'en' (already statically loaded)", async () => {
    const spy = jest.spyOn(i18n, "addResourceBundle");
    await loadLanguage("en");
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it("always has 'en' bundle available (statically bundled)", () => {
    expect(i18n.hasResourceBundle("en", "translation")).toBe(true);
  });

  it("loads and registers a new language bundle", async () => {
    expect(i18n.hasResourceBundle("fr", "translation")).toBe(false);
    await loadLanguage("fr");
    expect(i18n.hasResourceBundle("fr", "translation")).toBe(true);
  });

  it("does not call addResourceBundle if language is already cached", async () => {
    await loadLanguage("fr");
    const spy = jest.spyOn(i18n, "addResourceBundle");
    await loadLanguage("fr");
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });

  it("loads multiple different languages independently", async () => {
    await loadLanguage("fr");
    await loadLanguage("ja");
    expect(i18n.hasResourceBundle("fr", "translation")).toBe(true);
    expect(i18n.hasResourceBundle("ja", "translation")).toBe(true);
  });

  it("maps zh locale aliases to the zh-Hans translation bundle", async () => {
    expect(i18n.hasResourceBundle("zh-Hans", "translation")).toBe(false);
    await loadLanguage("zh");
    expect(i18n.hasResourceBundle("zh-Hans", "translation")).toBe(true);
  });
});

describe("normalizeLanguageCode", () => {
  it("maps browser zh locales to zh-Hans", () => {
    expect(normalizeLanguageCode("zh")).toBe("zh-Hans");
    expect(normalizeLanguageCode("zh-CN")).toBe("zh-Hans");
    expect(normalizeLanguageCode("zh-Hans")).toBe("zh-Hans");
  });

  it("falls back to the base language when supported", () => {
    expect(normalizeLanguageCode("pt-BR")).toBe("pt");
  });

  it("falls back to the default language when unsupported", () => {
    expect(normalizeLanguageCode("it-IT")).toBe(DEFAULT_LANGUAGE);
    expect(normalizeLanguageCode(undefined)).toBe(DEFAULT_LANGUAGE);
  });
});
