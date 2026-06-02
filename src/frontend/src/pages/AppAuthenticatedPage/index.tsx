import { Outlet } from "react-router-dom";
import { useCustomPostAuth } from "@/customization/hooks/use-custom-post-auth";

/**
 * 认证后的应用页面包装组件
 * 执行认证后的初始化操作，并渲染子路由内容
 */
export function AppAuthenticatedPage() {
  useCustomPostAuth();

  return <Outlet />;
}
