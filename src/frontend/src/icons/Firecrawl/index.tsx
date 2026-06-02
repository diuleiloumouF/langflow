// Firecrawl 图标组件 - 用于 Firecrawl 网页爬虫服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgFirecrawlLogo from "./FirecrawlLogo";

export const FirecrawlIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgFirecrawlLogo ref={ref} {...props} />;
});
