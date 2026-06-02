import { useEffect } from "react";
import {
  IS_AUTO_LOGIN,
  LANGFLOW_ACCESS_TOKEN_EXPIRE_SECONDS,
  LANGFLOW_ACCESS_TOKEN_EXPIRE_SECONDS_ENV,
} from "@/constants/constants";
import { useRefreshAccessToken } from "@/controllers/API/queries/auth";
import { CustomNavigate } from "@/customization/components/custom-navigate";
import useAuthStore from "@/stores/authStore";

/**
 * 通用受保护路由守卫组件
 * 用于保护需要登录才能访问的页面。
 * - 自动刷新访问令牌，保持会话有效
 * - 未认证时重定向到登录页面，并携带当前路径作为重定向参数
 * - 已认证时正常渲染子组件
 */
export const ProtectedRoute = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const { mutate: mutateRefresh } = useRefreshAccessToken(); // 刷新访问令牌的突变函数
  const autoLogin = useAuthStore((state) => state.autoLogin);
  const isAutoLoginEnv = IS_AUTO_LOGIN; // 环境变量中是否启用自动登录
  const testMockAutoLogin = sessionStorage.getItem("testMockAutoLogin"); // 测试用的模拟自动登录标记

  // 判断是否需要重定向到登录页
  const shouldRedirect =
    !isAuthenticated &&
    autoLogin !== undefined &&
    (!autoLogin || !isAutoLoginEnv);

  // 定时刷新访问令牌，保持用户会话有效
  useEffect(() => {
    // 优先使用环境变量中的过期时间，否则使用默认值
    const envRefreshTime = LANGFLOW_ACCESS_TOKEN_EXPIRE_SECONDS_ENV;
    const automaticRefreshTime = LANGFLOW_ACCESS_TOKEN_EXPIRE_SECONDS;

    // 计算令牌刷新间隔时间
    const accessTokenTimer = isNaN(envRefreshTime)
      ? automaticRefreshTime
      : envRefreshTime;

    // 执行令牌刷新的回调函数
    const intervalFunction = () => {
      mutateRefresh();
    };

    // 非自动登录模式下，已认证时启动定时刷新
    if (autoLogin !== undefined && !autoLogin && isAuthenticated) {
      const intervalId = setInterval(intervalFunction, accessTokenTimer * 1000);
      intervalFunction(); // 立即执行一次刷新
      return () => clearInterval(intervalId); // 组件卸载时清除定时器
    }
  }, [isAuthenticated]);

  if (shouldRedirect || testMockAutoLogin) {
    const currentPath = window.location.pathname; // 获取当前页面路径
    const isHomePath = currentPath === "/" || currentPath === "/flows"; // 是否在首页或流程列表页
    const isLoginPage = location.pathname.includes("login"); // 是否在登录页
    return (
      <CustomNavigate
        to={
          "/login" +
          (!isHomePath && !isLoginPage ? "?redirect=" + currentPath : "")
        }
        replace
      />
    );
  } else {
    return children;
  }
};
