// Maritalk 图标组件 - 用于 Maritalk AI 对话服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgMaritalkIcon from "./MaritalkIcon";

export const MaritalkIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgMaritalkIcon ref={ref} {...props} />;
});
