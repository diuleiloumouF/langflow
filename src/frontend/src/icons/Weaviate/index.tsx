// Weaviate 图标组件 - 用于 Weaviate 向量搜索引擎相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgWeaviate from "./Weaviate";

export const WeaviateIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgWeaviate ref={ref} {...props} />;
});
