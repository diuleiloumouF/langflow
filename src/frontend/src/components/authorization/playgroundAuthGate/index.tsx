import { useContext, useEffect, useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import { AuthContext } from "@/contexts/authContext";
import {
  useGetAuthSession,
  useGetAutoLogin,
} from "@/controllers/API/queries/auth";
import { LoadingPage } from "@/pages/LoadingPage";
import useAuthStore from "@/stores/authStore";
import type { Users } from "@/types/api";

/**
 * Playground 认证门控组件
 * 用于保护 Playground 页面的访问权限。
 * - 获取认证会话信息并同步到 AuthContext 和 Zustand 状态
 * - 认证检查完成前显示加载页面
 * - 未认证时重定向到登录页面
 * - 已认证时渲染子组件（Playground 内容）
 */
export function PlaygroundAuthGate({
  children,
}: {
  children: React.ReactNode;
}) {
  const { id } = useParams();
  const { setUserData, storeApiKey } = useContext(AuthContext);
  const setIsAuthenticated = useAuthStore((state) => state.setIsAuthenticated);
  const setIsAdmin = useAuthStore((state) => state.setIsAdmin);
  const autoLogin = useAuthStore((state) => state.autoLogin);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const [sessionProcessed, setSessionProcessed] = useState(false); // 标记会话是否已处理完成

  // 获取认证会话数据和自动登录配置
  const { data: sessionData, isFetched: isSessionFetched } =
    useGetAuthSession();
  const { isFetched: isAutoLoginFetched } = useGetAutoLogin();

  // 同步会话数据到认证状态
  useEffect(() => {
    if (!isSessionFetched) return; // 等待会话数据加载完成

    if (sessionData?.authenticated && sessionData.user) {
      // Set in both AuthContext (for components using useContext) and Zustand
      // store (for hooks like useGetFlowId and isAuthenticatedPlayground).
      // Both must be kept in sync — clearing one without the other causes stale state.
      const user = sessionData.user as Users;
      setUserData(user);
      useAuthStore.getState().setUserData(user);
      setIsAuthenticated(true);
      setIsAdmin(sessionData.user.is_superuser || false);
      if (sessionData.store_api_key) {
        storeApiKey(sessionData.store_api_key);
      }
    } else if (sessionData && !sessionData.authenticated) {
      setIsAuthenticated(false); // 会话未认证时更新状态
    }
    setSessionProcessed(true); // 标记会话处理完成
  }, [sessionData, isSessionFetched]);

  // 判断认证检查是否已完成
  const isAuthCheckComplete =
    (isAutoLoginFetched || isAuthenticated) && sessionProcessed;

  if (!isAuthCheckComplete) {
    return <LoadingPage />;
  }

  if (autoLogin === false && !isAuthenticated) {
    const currentPath = `/playground/${id}/`;
    return <Navigate to={`/login?redirect=${currentPath}`} replace />;
  }

  return <>{children}</>;
}
