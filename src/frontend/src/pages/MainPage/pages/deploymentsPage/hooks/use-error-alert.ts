import { useCallback } from "react";
import { getAxiosErrorMessage } from "@/controllers/API/helpers/get-axios-error-message";
import useAlertStore from "@/stores/alertStore";

/**
 * 错误提示 Hook
 * 封装错误提示的显示逻辑，自动解析 Axios 错误消息
 */
export function useErrorAlert() {
  const setErrorData = useAlertStore((s) => s.setErrorData);
  return useCallback(
    (title: string, err: unknown) => {
      setErrorData({ title, list: [getAxiosErrorMessage(err)] });
    },
    [setErrorData],
  );
}
