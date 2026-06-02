// Klipfolio 图标组件 - 用于 Klipfolio 数据仪表板平台相关组件的标识
import React, { forwardRef } from "react";
import KlipfolioIconSVG from "./klipfolio";

export const KlipfolioIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <KlipfolioIconSVG ref={ref} {...props} />;
});
