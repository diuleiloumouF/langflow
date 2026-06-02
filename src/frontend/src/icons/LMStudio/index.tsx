// LM Studio 图标组件 - 用于 LM Studio 本地模型运行平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgLMStudio from "./LMStudioIcon";

export const LMStudioIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgLMStudio ref={ref} {...props} />;
});
