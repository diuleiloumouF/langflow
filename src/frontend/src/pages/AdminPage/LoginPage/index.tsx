import { useQueryClient } from "@tanstack/react-query";
import { useContext, useState } from "react";
import { useTranslation } from "react-i18next";
import LangflowLogo from "@/assets/LangflowLogo.svg?react";
import { useLoginUser } from "@/controllers/API/queries/auth";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { CONTROL_LOGIN_STATE } from "../../../constants/constants";
import { AuthContext } from "../../../contexts/authContext";
import useAlertStore from "../../../stores/alertStore";
import type { LoginType } from "../../../types/api";
import type {
  inputHandlerEventType,
  loginInputStateType,
} from "../../../types/components";

/**
 * 管理员登录页面组件
 * 提供管理员专用的登录表单，包含用户名和密码输入框以及登录按钮
 */
export default function LoginAdminPage() {
  const [inputState, setInputState] =
    useState<loginInputStateType>(CONTROL_LOGIN_STATE);
  const { t } = useTranslation();
  const { login } = useContext(AuthContext);
  const queryClient = useQueryClient();
  const { password, username } = inputState;
  const setErrorData = useAlertStore((state) => state.setErrorData);
  // 处理表单输入变化，更新对应的输入状态
  function handleInput({
    target: { name, value },
  }: inputHandlerEventType): void {
    setInputState((prev) => ({ ...prev, [name]: value }));
  }

  const { mutate } = useLoginUser();

  // 执行管理员登录操作
  function signIn() {
    const user: LoginType = {
      username: username,
      password: password,
    };

    mutate(user, {
      onSuccess: (res) => {
        login(res.access_token, "login", res.refresh_token);
        queryClient.clear();
      },
      onError: (error) => {
        setErrorData({
          title: t("errors.signin"),
          list: [error["response"]["data"]["detail"]],
        });
      },
    });
  }

  return (
    <div className="flex h-full w-full flex-col items-center justify-center bg-muted">
      <div className="flex w-72 flex-col items-center justify-center gap-2">
        <LangflowLogo title="Langflow logo" className="h-10 w-10 scale-[1.5]" />
        <span className="mb-6 text-2xl font-semibold text-primary">
          {t("auth.adminTitle")}
        </span>
        <Input
          onChange={({ target: { value } }) => {
            handleInput({ target: { name: "username", value } });
          }}
          className="bg-background"
          placeholder={t("auth.usernamePlaceholder")}
        />
        <Input
          type="password"
          onChange={({ target: { value } }) => {
            handleInput({ target: { name: "password", value } });
          }}
          className="bg-background"
          placeholder={t("auth.passwordPlaceholder")}
        />
        <Button
          onClick={() => {
            signIn();
          }}
          variant="default"
          className="w-full"
        >
          {t("auth.adminLoginButton")}
        </Button>
      </div>
    </div>
  );
}
