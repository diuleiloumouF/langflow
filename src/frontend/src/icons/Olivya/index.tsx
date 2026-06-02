// Olivya 图标组件 - 用于 Olivya AI 服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import OlivyaSVG from "./olivya";

export const OlivyaIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <OlivyaSVG ref={ref} {...props} />;
});
