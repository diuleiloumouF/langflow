// MCP 图标组件 - 用于 Model Context Protocol (模型上下文协议) 相关组件的标识
import React, { forwardRef } from "react";
import SvgMcpIcon from "./McpIcon";

export const McpIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgMcpIcon ref={ref} {...props} />;
  },
);
