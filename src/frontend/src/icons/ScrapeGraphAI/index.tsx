// ScrapeGraph AI 图标组件 - 用于 ScrapeGraph AI 智能爬虫服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import ScrapeGraphAI from "./ScrapeGraphAI";

export const ScrapeGraph = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <ScrapeGraphAI ref={ref} {...props} />;
});
