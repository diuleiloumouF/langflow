// Flexisign 图标组件 - 用于 Flexisign 电子签名服务相关组件的标识
import React, { forwardRef } from "react";
import FlexisignIconSVG from "./flexisign";

export const FlexisignIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <FlexisignIconSVG ref={ref} {...props} />;
});
