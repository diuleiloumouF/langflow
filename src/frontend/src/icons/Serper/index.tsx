// Serper 图标组件 - 用于 Serper Google 搜索 API 服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSerper from "./Serper";

export const SerperIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgSerper ref={ref} {...props} />;
});
