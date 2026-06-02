import { useIsFetching, useIsMutating } from "@tanstack/react-query";
import type { AxiosError } from "axios";
import { useEffect, useState } from "react";
import { useGetHealthQuery } from "@/controllers/API/queries/health";
import useFlowStore from "@/stores/flowStore";
import useFlowsManagerStore from "@/stores/flowsManagerStore";
import { useUtilityStore } from "@/stores/utilityStore";

/**
 * 服务器健康检查 Hook
 * 定期检查后端服务的健康状态，在服务器繁忙时（503/429）执行指数退避重试
 * @returns healthCheckTimeout - 健康检查超时状态，用于决定是否显示错误页面
 * @returns refetch - 手动触发健康检查的方法
 * @returns fetchingHealth - 是否正在获取健康状态
 */
export function useHealthCheck() {
  const healthCheckMaxRetries = useFlowsManagerStore(
    (state) => state.healthCheckMaxRetries,
  );

  const healthCheckTimeout = useUtilityStore(
    (state) => state.healthCheckTimeout,
  );

  const isMutating = useIsMutating();
  const isFetching = useIsFetching({
    predicate: (query) => query.queryKey[0] !== "useGetHealthQuery",
  });
  const isBuilding = useFlowStore((state) => state.isBuilding);

  // 当有正在进行的请求或流程构建时，暂停健康检查
  const disabled = isMutating || isFetching || isBuilding;

  const {
    isFetching: fetchingHealth,
    isError: isErrorHealth,
    error,
    refetch,
  } = useGetHealthQuery({ enableInterval: !disabled });
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    // 检查服务器是否处于繁忙状态（503 服务不可用或 429 请求过多）
    const isServerBusy =
      (error as AxiosError)?.response?.status === 503 ||
      (error as AxiosError)?.response?.status === 429;

    if (isServerBusy && isErrorHealth && !disabled) {
      const maxRetries = healthCheckMaxRetries;
      if (retryCount < maxRetries) {
        const delay = 2 ** retryCount * 1000;
        const timer = setTimeout(() => {
          refetch();
          setRetryCount(retryCount + 1);
        }, delay);

        return () => clearTimeout(timer);
      }
    } else {
      setRetryCount(0);
    }
  }, [isErrorHealth, retryCount, refetch]);

  return { healthCheckTimeout, refetch, fetchingHealth };
}
