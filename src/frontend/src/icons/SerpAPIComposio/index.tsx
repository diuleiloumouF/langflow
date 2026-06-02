// SerpAPI Composio 图标组件 - 用于 SerpAPI 通过 Composio 集成的搜索服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSerpSearchAPI from "./SerpSearch";

export const SerpSearchIconComposio = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgSerpSearchAPI ref={ref} {...props} />;
});
