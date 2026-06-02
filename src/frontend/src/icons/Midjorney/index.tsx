// Midjourney 图标组件 - 用于 Midjourney AI 图像生成服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgMidjourneyEmblem from "./MidjourneyEmblem";

export const MidjourneyIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgMidjourneyEmblem ref={ref} {...props} />;
});
