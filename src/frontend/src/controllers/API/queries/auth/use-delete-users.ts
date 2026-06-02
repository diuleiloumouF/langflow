import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

/**
 * 删除用户参数接口
 */
interface DeleteUserParams {
  user_id: string;
}

/**
 * 删除用户的自定义 Hook
 * @returns 删除用户的 mutation 函数
 */
export const useDeleteUsers: useMutationFunctionType<
  undefined,
  DeleteUserParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  const deleteMessage = async ({ user_id }: DeleteUserParams): Promise<any> => {
    const res = await api.delete(`${getURL("USERS")}/${user_id}`);
    return res.data;
  };

  const mutation: UseMutationResult<DeleteUserParams, any, DeleteUserParams> =
    mutate(["useDeleteUsers"], deleteMessage, options);

  return mutation;
};
