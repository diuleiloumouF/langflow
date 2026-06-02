// Zep Memory 图标组件 - 用于 Zep 记忆管理服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgZepMemory from "./ZepMemory";

export const ZepMemoryIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgZepMemory ref={ref} {...props} />;
});
