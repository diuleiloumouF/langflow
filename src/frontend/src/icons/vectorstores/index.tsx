// VectorStores 图标组件 - 用于向量数据库存储功能相关组件的标识
import React, { forwardRef } from "react";
import SvgVectorStores from "./VectorStores";

export const VectorStoresIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgVectorStores ref={ref} {...props} />;
});
