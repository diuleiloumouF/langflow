// Capsule CRM 图标组件 - 用于 Capsule CRM 客户关系管理平台相关组件的标识
import React, { forwardRef } from "react";
import CapsulecrmIconSVG from "./capsulecrm";

export const CapsulecrmIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <CapsulecrmIconSVG ref={ref} {...props} />;
});
