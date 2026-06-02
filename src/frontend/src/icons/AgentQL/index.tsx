// AgentQL 图标组件 - 用于 AgentQL 智能体查询语言相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgAgentQL from "./AgentQL";

export const AgentQLIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgAgentQL ref={ref} {...props} />;
});
