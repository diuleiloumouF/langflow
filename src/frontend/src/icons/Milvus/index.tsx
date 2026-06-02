// Milvus 图标组件 - 用于 Milvus 向量数据库相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgMilvus from "./Milvus";

export const MilvusIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgMilvus ref={ref} {...props} />;
});
