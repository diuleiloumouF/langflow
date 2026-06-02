// Share2 图标组件 - 用于分享功能的备选样式相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgShare2 from "./Share2";

export const Share2Icon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgShare2 ref={ref} {...props} />;
});
