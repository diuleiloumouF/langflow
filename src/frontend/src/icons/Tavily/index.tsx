// Tavily 图标组件 - 用于 Tavily AI 搜索服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import Tavily from "./Tavily";

export const TavilyIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <Tavily ref={ref} {...props} />;
});
