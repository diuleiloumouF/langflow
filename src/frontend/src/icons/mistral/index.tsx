// Mistral 图标组件 - 用于 Mistral AI 大语言模型服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgMistralIcon from "./mistralIcon";

export const MistralIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgMistralIcon ref={ref} {...props} />;
});
