import { ErrorBoundary } from "react-error-boundary";
import { Outlet } from "react-router-dom";
import AlertDisplayArea from "@/alerts/displayArea";
import CrashErrorComponent from "@/components/common/crashErrorComponent";
import { GenericErrorComponent } from "./components/GenericErrorComponent";
import { useHealthCheck } from "./hooks/use-health-check";

/**
 * 应用根包装组件
 * 提供错误边界、健康检查和全局提示展示功能
 * 包含崩溃错误处理、服务器健康状态检测以及子路由渲染
 */
export function AppWrapperPage() {
  const { healthCheckTimeout, fetchingHealth, refetch } = useHealthCheck();

  return (
    <div className="flex h-full w-full flex-col">
      <ErrorBoundary
        onReset={() => {
          // any reset function
        }}
        FallbackComponent={CrashErrorComponent}
      >
        <>
          <GenericErrorComponent
            healthCheckTimeout={healthCheckTimeout}
            fetching={fetchingHealth}
            retry={refetch}
          />
          <Outlet />
        </>
      </ErrorBoundary>
      <div className="app-div">
        <AlertDisplayArea />
      </div>
    </div>
  );
}
