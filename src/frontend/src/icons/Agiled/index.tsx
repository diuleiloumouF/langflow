// Agiled 图标组件 - 用于 Agiled 项目管理平台相关组件的标识
import React, { forwardRef } from "react";
import AgiledIconSVG from "./agiled";

export const AgiledIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <AgiledIconSVG ref={ref} {...props} />;
});
