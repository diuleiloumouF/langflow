// Google 图标组件 - 用于 Google 服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgGoogle from "./Google";

export const GoogleIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgGoogle ref={ref} {...props} />;
});
