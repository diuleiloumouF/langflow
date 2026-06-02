import { useContext, useEffect, useMemo } from "react";
import { Outlet } from "react-router-dom";
import { AuthContext } from "@/contexts/authContext";
import {
  useGetAuthSession,
  useGetAutoLogin,
} from "@/controllers/API/queries/auth";
import { useGetConfig } from "@/controllers/API/queries/config/use-get-config";
import { useGetBasicExamplesQuery } from "@/controllers/API/queries/flows/use-get-basic-examples";
import { useGetFoldersQuery } from "@/controllers/API/queries/folders/use-get-folders";
import { useGetTagsQuery } from "@/controllers/API/queries/store";
import { useGetGlobalVariables } from "@/controllers/API/queries/variables";
import { useGetVersionQuery } from "@/controllers/API/queries/version";
import { CustomLoadingPage } from "@/customization/components/custom-loading-page";
import { useCustomPrimaryLoading } from "@/customization/hooks/use-custom-primary-loading";
import useAuthStore from "@/stores/authStore";
import { useDarkStore } from "@/stores/darkStore";
import useFlowsManagerStore from "@/stores/flowsManagerStore";
import { LoadingPage } from "../LoadingPage";

/**
 * 应用初始化页面组件
 * 负责应用启动时的认证状态恢复、配置加载、数据预取等初始化工作
 * 在初始化完成前显示加载页面，完成后渲染子路由
 */
export function AppInitPage() {
  // 刷新 GitHub star 数量
  const refreshStars = useDarkStore((state) => state.refreshStars);
  const refreshDiscordCount = useDarkStore(
    (state) => state.refreshDiscordCount,
  );
  const isLoading = useFlowsManagerStore((state) => state.isLoading);
  const { setUserData, storeApiKey } = useContext(AuthContext);
  const setIsAuthenticated = useAuthStore((state) => state.setIsAuthenticated);
  const setIsAdmin = useAuthStore((state) => state.setIsAdmin);
  const autoLogin = useAuthStore((state) => state.autoLogin);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const { isFetched: isLoaded } = useCustomPrimaryLoading();

  // 在应用初始化时验证会话，从 HttpOnly cookies 恢复认证状态
  // Validate session on app init to restore auth state from HttpOnly cookies
  const { data: sessionData, isFetched: isSessionFetched } = useGetAuthSession({
    enabled: isLoaded,
  });

  const { isFetched } = useGetAutoLogin({ enabled: isLoaded });

  // 仅在用户已认证时获取需要认证的接口数据
  // Only fetch authenticated endpoints when user is authenticated
  // (either via auto-login or manual login)
  const isAuthReady = autoLogin === true || isAuthenticated;

  useGetVersionQuery({ enabled: isFetched });
  const { isFetched: isConfigFetched } = useGetConfig({
    enabled: isFetched && isAuthReady,
  });
  useGetGlobalVariables({ enabled: isFetched && isAuthReady });
  useGetTagsQuery({ enabled: isFetched && isAuthReady });
  useGetFoldersQuery({ enabled: isFetched && isAuthReady });
  const { isFetched: isExamplesFetched, refetch: refetchExamples } =
    useGetBasicExamplesQuery();

  // 当会话数据可用时更新认证状态
  // Update auth state when session data is available
  useEffect(() => {
    if (sessionData?.authenticated && sessionData.user) {
      setUserData(sessionData.user);
      setIsAuthenticated(true);
      setIsAdmin(sessionData.user.is_superuser || false);
      if (sessionData.store_api_key) {
        storeApiKey(sessionData.store_api_key);
      }
    } else if (sessionData && !sessionData.authenticated) {
      // Explicitly not authenticated
      setIsAuthenticated(false);
    }
  }, [sessionData]);

  useEffect(() => {
    if (isFetched) {
      refreshStars();
      refreshDiscordCount();
    }

    if (isConfigFetched) {
      refetchExamples();
    }
  }, [isFetched, isConfigFetched]);

  // 判断会话是否已准备就绪
  const isSessionReady = useMemo(
    () => isAuthenticated || autoLogin || isSessionFetched,
    [autoLogin, isSessionFetched, isAuthenticated],
  );

  // 自动登录"完成"的条件：
  // Auto-login is "complete" if:
  // - The query actually ran (isFetched), OR
  // - We're already authenticated (so we skipped auto-login intentionally)
  const isAutoLoginComplete = isFetched || isAuthenticated;

  // 应用是否完全准备就绪
  const isReady = isAutoLoginComplete && isExamplesFetched && isSessionReady;

  return (
    <>
      {isLoaded ? (
        (isLoading || !isReady) && <LoadingPage overlay />
      ) : (
        <CustomLoadingPage />
      )}
      {isReady && <Outlet />}
    </>
  );
}
