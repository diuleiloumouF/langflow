// Finage 图标组件 - 用于 Finage 金融数据 API 服务相关组件的标识
import React, { forwardRef } from "react";
import FinageIconSVG from "./finage";

export const FinageIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <FinageIconSVG ref={ref} {...props} />;
});
