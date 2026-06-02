import { CustomNavigate } from "@/customization/components/custom-navigate";
import { consumeRedirectUrl } from "@/hooks/use-sanitize-redirect-url";
import useAuthStore from "@/stores/authStore";

/**
 * 登录页面路由守卫组件
 * 防止已登录用户再次访问登录页面。
 * - 已认证或自动登录模式下，重定向到之前的页面或首页
 * - 未认证时正常渲染登录页面
 */
export const ProtectedLoginRoute = ({ children }) => {
  const autoLogin = useAuthStore((state) => state.autoLogin);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (autoLogin === true || isAuthenticated) {
    // 已登录时，优先跳转到URL中的重定向路径，否则跳转到首页
    const urlParams = new URLSearchParams(window.location.search);
    const redirectPath = urlParams.get("redirect") || consumeRedirectUrl(); // 从URL参数或session中获取重定向路径

    if (redirectPath) {
      return <CustomNavigate to={redirectPath} replace />;
    }
    return <CustomNavigate to="/home" replace />;
  }

  return children;
};
