import type { UseMutationResult } from "@tanstack/react-query";
import useAuthStore from "@/stores/authStore";
import type { Users, useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
/**
 * 获取当前用户数据的自定义 Hook
 * 从后端获取用户信息并更新到全局状态
 * @returns 获取用户数据的 mutation 函数
 */
export const useGetUserData: useMutationFunctionType<undefined, any> = (
  options?,
) => {
  const setUserData = useAuthStore((state) => state.setUserData);
  const { mutate } = UseRequestProcessor();

  const getUserData = async () => {
    const response = await api.get<Users>(`${getURL("USERS")}/whoami`);
    setUserData(response["data"]);
    return response["data"];
  };

  const mutation: UseMutationResult = mutate(
    ["useGetUserData"],
    getUserData,
    options,
  );

  return mutation;
};
