// AssemblyAI 图标组件 - 用于 AssemblyAI 语音识别服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import AssemblyAISVG from "./AssemblyAI";

export const AssemblyAIIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <AssemblyAISVG ref={ref} {...props} />;
});
