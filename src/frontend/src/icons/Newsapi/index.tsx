// News API 图标组件 - 用于 News API 新闻聚合服务相关组件的标识
import React, { forwardRef } from "react";
import NewsapiIconSVG from "./newsapi";

export const NewsapiIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <NewsapiIconSVG ref={ref} {...props} />;
});
