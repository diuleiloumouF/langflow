// LiteLLM 图标组件 - 用于 LiteLLM 代理服务器相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgLiteLLM from "./LiteLLMIcon";

export const LiteLLMIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgLiteLLM ref={ref} {...props} />;
});
