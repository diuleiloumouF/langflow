// CometAPI 图标组件 - 用于 Comet API 监控服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgCometAPI from "./cometapi";

export const CometAPIIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgCometAPI ref={ref} {...props} />;
});
