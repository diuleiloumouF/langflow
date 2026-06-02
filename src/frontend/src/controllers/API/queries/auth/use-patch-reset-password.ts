import type { UseMutationResult } from "@tanstack/react-query";
import type { resetPasswordType, useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

/**
 * 重置密码参数接口
 */
interface resetPasswordParams {
  user_id: string;
  password: resetPasswordType;
}

/**
 * 重置用户密码的自定义 Hook
 * @returns 重置密码的 mutation 函数
 */
export const useResetPassword: useMutationFunctionType<
  undefined,
  resetPasswordParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function resetPassword({
    user_id,
    password,
  }: resetPasswordParams): Promise<any> {
    const res = await api.patch(
      `${getURL("USERS")}/${user_id}/reset-password`,
      password,
    );
    return res.data;
  }

  const mutation: UseMutationResult<
    resetPasswordParams,
    any,
    resetPasswordParams
  > = mutate(["useResetPassword"], resetPassword, options);

  return mutation;
};
