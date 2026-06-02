// OpenSearch 图标组件 - 用于 OpenSearch 开源搜索引擎相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import OpenSearchSVG from "./OpenSearch";

export const OpenSearch = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <OpenSearchSVG ref={ref} {...props} />;
});
