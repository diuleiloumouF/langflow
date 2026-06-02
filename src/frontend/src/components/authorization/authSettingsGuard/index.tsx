import { CustomNavigate } from "@/customization/components/custom-navigate";
import { ENABLE_PROFILE_ICONS } from "@/customization/feature-flags";
import useAuthStore from "@/stores/authStore";
import { useStoreStore } from "@/stores/storeStore";

/**
 * 设置页面路由守卫组件
 * 控制通用设置页面的显示条件。
 * - 当启用了头像图标、商店功能或非自动登录模式时，显示通用设置
 * - 否则重定向到全局变量设置页面
 */
export const AuthSettingsGuard = ({ children }) => {
  const autoLogin = useAuthStore((state) => state.autoLogin);
  const hasStore = useStoreStore((state) => state.hasStore);

  // Hides the General settings if there is nothing to show
  const showGeneralSettings = ENABLE_PROFILE_ICONS || hasStore || !autoLogin;

  if (showGeneralSettings) {
    return children;
  } else {
    return <CustomNavigate replace to="/settings/global-variables" />;
  }
};
