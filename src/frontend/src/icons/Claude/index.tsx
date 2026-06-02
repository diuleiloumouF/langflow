// Claude 图标组件 - 用于 Claude AI 助手相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import ClaudeSVG from "./Claude";

export const ClaudeIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <ClaudeSVG ref={ref} {...props} />;
});
