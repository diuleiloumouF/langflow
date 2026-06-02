import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { SUPPORTED_LANGUAGES } from "@/constants/languages";
import { loadLanguage } from "@/i18n";
import { useTypesStore } from "@/stores/typesStore";

/**
 * 语言选择器组件
 * 提供下拉选择框切换应用语言，切换时会清除类型缓存并重新获取数据。
 */
export const LanguageSelector = () => {
  const { t, i18n } = useTranslation();
  const queryClient = useQueryClient();
  const setTypes = useTypesStore((state) => state.setTypes);

  // 处理语言切换
  const handleChange = async (code: string) => {
    await loadLanguage(code);
    i18n.changeLanguage(code);
    localStorage.setItem("languagePreference", code);
    setTypes({});
    queryClient.invalidateQueries({ queryKey: ["useGetTypes"] });
  };

  return (
    <select
      aria-label={t("settings.languageSelectAriaLabel")}
      value={i18n.language}
      onChange={(e) => handleChange(e.target.value)}
      className="rounded border border-border bg-background px-1 py-0.5 text-sm text-foreground"
    >
      {SUPPORTED_LANGUAGES.map((lang) => (
        <option key={lang.code} value={lang.code}>
          {lang.label}
        </option>
      ))}
    </select>
  );
};

export default LanguageSelector;
