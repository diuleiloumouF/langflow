// Anthropic 图标组件 - 用于 Anthropic AI 服务相关组件的标识
import React, { forwardRef } from "react";
import SvgAnthropicBox from "./Anthropic";

export const AnthropicIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgAnthropicBox ref={ref} {...props} />;
});
