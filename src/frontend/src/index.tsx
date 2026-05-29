import "./i18n";
import ReactDOM from "react-dom/client";
import { DEFAULT_LANGUAGE, normalizeLanguageCode } from "./constants/languages";
import i18n, { loadLanguage } from "./i18n";
import reportWebVitals from "./reportWebVitals";

import "./style/classes.css";
// @ts-ignore
import "./style/index.css";
// @ts-ignore
import "./App.css";
import "./style/applies.css";

// @ts-ignore
import App from "./customization/custom-App";

const detectedLang = normalizeLanguageCode(
  localStorage.getItem("languagePreference") ||
    navigator.language.split("-")[0] ||
    DEFAULT_LANGUAGE,
);

loadLanguage(detectedLang).then(() => {
  i18n.changeLanguage(detectedLang);
  const root = ReactDOM.createRoot(
    document.getElementById("root") as HTMLElement,
  );
  root.render(<App />);
  reportWebVitals();
});
