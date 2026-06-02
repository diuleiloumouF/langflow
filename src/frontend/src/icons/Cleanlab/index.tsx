// Cleanlab 图标组件 - 用于 Cleanlab 数据质量服务相关组件的标识
import React, { forwardRef } from "react";
import SvgCleanlab from "./Cleanlab";

export const CleanlabIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgCleanlab ref={ref} {...props} />;
});
