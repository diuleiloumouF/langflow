// Freshdesk 图标组件 - 用于 Freshdesk 客户服务管理平台相关组件的标识
import React, { forwardRef } from "react";
import FreshdeskIconSVG from "./freshdesk";

export const FreshdeskIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <FreshdeskIconSVG ref={ref} {...props} />;
});
