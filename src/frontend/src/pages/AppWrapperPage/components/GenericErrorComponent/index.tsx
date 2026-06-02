import { useTranslation } from "react-i18next";
import TimeoutErrorComponent from "@/components/common/timeoutErrorComponent";
import CustomFetchErrorComponent from "@/customization/components/custom-fetch-error-component";

/**
 * 通用错误组件
 * 根据健康检查的状态显示不同类型的错误提示页面
 * @param healthCheckTimeout - 健康检查超时状态（"serverDown" | "timeout" | null）
 * @param fetching - 是否正在获取健康状态
 * @param retry - 重试健康检查的回调函数
 */
export function GenericErrorComponent({ healthCheckTimeout, fetching, retry }) {
  const { t } = useTranslation();
  switch (healthCheckTimeout) {
    case "serverDown":
      return (
        <CustomFetchErrorComponent
          description={t("misc.fetchErrorDescription")}
          message={t("misc.fetchErrorMessage")}
          openModal={true}
          setRetry={retry}
          isLoadingHealth={fetching}
        ></CustomFetchErrorComponent>
      );
    case "timeout":
      return (
        <TimeoutErrorComponent
          description={t("misc.timeoutErrorMessage")}
          message={t("misc.timeoutErrorDescription")}
          openModal={true}
          setRetry={retry}
          isLoadingHealth={fetching}
        ></TimeoutErrorComponent>
      );
    default:
      return <></>;
  }
}
