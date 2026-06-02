// Needle 图标组件 - 用于 Needle 数据检索服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import NeedleSvg from "./needle-icon.svg?react";

export const NeedleIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <NeedleSvg ref={ref} {...props} />;
});
