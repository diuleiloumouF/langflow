// PowerPoint 图标组件 - 用于 Microsoft PowerPoint 演示文稿相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgPowerPoint from "./PowerPoint";

export const PowerPointIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgPowerPoint ref={ref} {...props} />;
});
