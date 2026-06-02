// Globe Ok 图标组件 - 用于网络连接正常状态指示的标识
import type React from "react";
import { forwardRef } from "react";
import SvgGlobeOkIcon from "./globe-ok";

export const GlobeOkIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgGlobeOkIcon ref={ref} {...props} />;
});
