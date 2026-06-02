/**
 * 重复请求检查模块
 * 检测并阻止短时间内重复发送的相同请求
 */
import { AUTHORIZED_DUPLICATE_REQUESTS } from "../../../constants/constants";

/**
 * 检查请求是否为重复请求并存储当前请求信息
 * 用于防止用户快速点击导致的重复请求问题
 * @param config - Axios 请求配置
 * @throws 如果检测到重复请求则抛出错误
 */
export function checkDuplicateRequestAndStoreRequest(config) {
  const lastUrl = localStorage.getItem("lastUrlCalled");
  const lastMethodCalled = localStorage.getItem("lastMethodCalled");
  const lastRequestTime = localStorage.getItem("lastRequestTime");
  const lastCurrentUrl = localStorage.getItem("lastCurrentUrl");

  const currentUrl = window.location.pathname;
  const currentTime = Date.now();
  const isContained = AUTHORIZED_DUPLICATE_REQUESTS.some((request) =>
    config?.url!.includes(request),
  );

  if (
    config?.url === lastUrl &&
    !isContained &&
    lastMethodCalled === config.method &&
    lastMethodCalled === "get" && // Assuming you want to check only for GET requests
    lastRequestTime &&
    currentTime - parseInt(lastRequestTime, 10) < 300 &&
    lastCurrentUrl === currentUrl
  ) {
    throw new Error("Duplicate request: " + lastUrl);
  }

  localStorage.setItem("lastUrlCalled", config.url ?? "");
  localStorage.setItem("lastMethodCalled", config.method ?? "");
  localStorage.setItem("lastRequestTime", currentTime.toString());
  localStorage.setItem("lastCurrentUrl", currentUrl);
}
