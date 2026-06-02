// Windsurf 图标组件 - 用于 Windsurf AI 代码编辑器相关组件的标识
import React, { forwardRef } from "react";
import SvgWindsurf from "./Windsurf";

export const WindsurfIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgWindsurf ref={ref} {...props} />;
});
