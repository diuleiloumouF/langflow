// Jotform 图标组件 - 用于 Jotform 在线表单构建平台相关组件的标识
import React, { forwardRef } from "react";
import JotformIconSVG from "./jotform";

export const JotformIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <JotformIconSVG ref={ref} {...props} />;
});
