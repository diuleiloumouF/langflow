import type { UseMutationResult } from "@tanstack/react-query";
import type { changeUser, useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

/**
 * 更新用户参数接口
 */
interface UpdateUserParams {
  user_id: string;
  user: changeUser;
}

/**
 * 更新用户信息的自定义 Hook
 * @returns 更新用户的 mutation 函数
 */
export const useUpdateUser: useMutationFunctionType<
  undefined,
  UpdateUserParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function updateUser({ user_id, user }: UpdateUserParams): Promise<any> {
    const res = await api.patch(`${getURL("USERS")}/${user_id}`, user);
    return res.data;
  }

  const mutation: UseMutationResult<UpdateUserParams, any, UpdateUserParams> =
    mutate(["useUpdateUser"], updateUser, options);

  return mutation;
};
