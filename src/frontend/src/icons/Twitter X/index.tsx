// Twitter X 图标组件 - 用于 Twitter (X) 社交媒体平台相关组件的标识
import React, { forwardRef } from "react";
import TwitterXSVG from "./TwitterX.jsx";

export const TwitterXIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <TwitterXSVG ref={ref} {...props} />;
});
