// SerpSearch 图标组件 - 用于 SerpSearch 搜索结果页面 API 服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSerpSearchAPI from "./SerpSearch";

export const SerpSearchIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgSerpSearchAPI ref={ref} {...props} />;
});
