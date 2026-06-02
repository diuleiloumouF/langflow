// Cohere 图标组件 - 用于 Cohere AI 语言模型服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgCohere from "./Cohere";

export const CohereIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgCohere ref={ref} {...props} />;
});
