// Agentics 图标组件 - 用于 Agentics AI 智能体平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgAgentics from "./Agentics";

export const AgenticsIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgAgentics ref={ref} {...props} />;
});
