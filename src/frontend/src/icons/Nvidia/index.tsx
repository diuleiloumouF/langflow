// Nvidia 图标组件 - 用于 Nvidia GPU 计算平台相关组件的标识
import React, { forwardRef } from "react";
import NvidiaSVG from "./nvidia";

export const NvidiaIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <NvidiaSVG ref={ref} {...props} />;
});
