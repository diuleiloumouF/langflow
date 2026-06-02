// AgentQL Composio 图标组件 - 用于 AgentQL 通过 Composio 集成的相关组件的标识
import React, { forwardRef } from "react";
import AgentqlIconSVG from "./agentql";

export const AgentqlIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <AgentqlIconSVG ref={ref} {...props} />;
});
