// Canvas 图标组件 - 用于 Canvas 协作白板平台相关组件的标识
import React, { forwardRef } from "react";
import CanvasIconSVG from "./canvas";

export const CanvasIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <CanvasIconSVG ref={ref} {...props} />;
});
