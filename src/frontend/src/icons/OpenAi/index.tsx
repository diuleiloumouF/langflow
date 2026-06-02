// OpenAI 图标组件 - 用于 OpenAI AI 服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgOpenAi from "./OpenAi";

export const OpenAiIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgOpenAi ref={ref} {...props} />;
});
