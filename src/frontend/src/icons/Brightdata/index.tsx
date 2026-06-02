// Bright Data 图标组件 - 用于 Bright Data 网络数据平台相关组件的标识
import React, { forwardRef } from "react";
import BrightdataIconSVG from "./brightdata";

export const BrightdataIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <BrightdataIconSVG ref={ref} {...props} />;
});
