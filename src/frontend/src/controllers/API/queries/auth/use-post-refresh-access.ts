import { IS_AUTO_LOGIN, LANGFLOW_REFRESH_TOKEN } from "@/constants/constants";
import useAuthStore from "@/stores/authStore";
import type { useMutationFunctionType } from "@/types/api";
import { cookieManager } from "@/utils/cookie-manager";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

/**
 * 刷新访问令牌响应接口
 */
interface IRefreshAccessToken {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/**
 * 刷新访问令牌的自定义 Hook
 * 用于在令牌过期时获取新的访问令牌
 * @returns 刷新令牌的 mutation 函数
 */
export const useRefreshAccessToken: useMutationFunctionType<
  undefined,
  undefined | void,
  IRefreshAccessToken
> = (options?) => {
  const { mutate } = UseRequestProcessor();
  const autoLogin = useAuthStore((state) => state.autoLogin);

  async function refreshAccess(): Promise<IRefreshAccessToken> {
    const res = await api.post<IRefreshAccessToken>(`${getURL("REFRESH")}`);
    cookieManager.set(LANGFLOW_REFRESH_TOKEN, res.data.refresh_token);

    return res.data;
  }

  const mutation = mutate(["useRefreshAccessToken"], refreshAccess, {
    ...options,
    retry: IS_AUTO_LOGIN || autoLogin ? 0 : 2,
  });

  return mutation;
};
