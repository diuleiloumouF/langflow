// AstraDB 图标组件 - 用于 DataStax AstraDB 云原生数据库相关组件的标识
import React, { forwardRef } from "react";
import AstraSVG from "./AstraDB";

export const AstraDBIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <AstraSVG ref={ref} {...props} />;
});
