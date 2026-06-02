// Brandfetch 图标组件 - 用于 Brandfetch 品牌数据 API 服务相关组件的标识
import React, { forwardRef } from "react";
import BrandfetchIconSVG from "./brandfetch";

export const BrandfetchIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <BrandfetchIconSVG ref={ref} {...props} />;
});
