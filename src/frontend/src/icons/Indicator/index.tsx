// Indicator 图标组件 - 用于状态指示器相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import { IndicatorComponent } from "./Indicator";

export const IndicatorIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{ className?: string }>
>((props, ref) => {
  return <IndicatorComponent ref={ref} {...props} />;
});
