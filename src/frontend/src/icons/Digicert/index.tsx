// Digicert 图标组件 - 用于 Digicert 数字证书和网络安全服务相关组件的标识
import React, { forwardRef } from "react";
import DigicertIconSVG from "./digicert";

export const DigicertIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <DigicertIconSVG ref={ref} {...props} />;
});
