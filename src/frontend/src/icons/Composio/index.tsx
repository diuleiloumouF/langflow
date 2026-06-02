// Composio 图标组件 - 用于 Composio 工具集成平台相关组件的标识
import React, { forwardRef } from "react";
import ComposioIconSVG from "./composio";

export const ComposioIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <ComposioIconSVG ref={ref} {...props} />;
});
