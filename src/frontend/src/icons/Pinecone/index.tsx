// Pinecone 图标组件 - 用于 Pinecone 向量数据库服务相关组件的标识
import React, { forwardRef } from "react";
import SvgPineconeLogo from "./PineconeLogo";

export const PineconeIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgPineconeLogo ref={ref} {...props} />;
});
