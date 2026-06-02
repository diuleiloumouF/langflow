import { useContext } from "react";
import { AuthContext } from "@/contexts/authContext";
import { CustomNavigate } from "@/customization/components/custom-navigate";
import { LoadingPage } from "@/pages/LoadingPage";
import useAuthStore from "@/stores/authStore";

/**
 * 管理员路由守卫组件
 * 仅允许已认证的管理员用户访问受保护的子路由。
 * - 未认证时显示加载页面
 * - 非管理员或自动登录模式下重定向到首页
 * - 管理员用户正常渲染子组件
 */
export const ProtectedAdminRoute = ({ children }) => {
  const { userData } = useContext(AuthContext);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const autoLogin = useAuthStore((state) => state.autoLogin);
  const isAdmin = useAuthStore((state) => state.isAdmin); // 是否为管理员

  if (!isAuthenticated) {
    return <LoadingPage />;
  } else if ((userData && !isAdmin) || autoLogin) {
    return <CustomNavigate to="/" replace />;
  } else {
    return children;
  }
};
