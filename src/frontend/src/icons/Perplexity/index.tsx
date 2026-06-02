// Perplexity 图标组件 - 用于 Perplexity AI 搜索引擎相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import PerplexitySVG from "./Perplexity";

export const PerplexityIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <PerplexitySVG ref={ref} {...props} />;
});
