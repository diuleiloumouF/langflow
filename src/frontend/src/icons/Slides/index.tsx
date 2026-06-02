// Slides 图标组件 - 用于演示文稿幻灯片相关组件的标识
import React, { forwardRef } from "react";
import SlidesIconSVG from "./slides";

export const SlidesIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SlidesIconSVG ref={ref} {...props} />;
});
