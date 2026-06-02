// Missive 图标组件 - 用于 Missive 团队协作邮件平台相关组件的标识
import React, { forwardRef } from "react";
import MissiveIconSVG from "./missive";

export const MissiveIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <span
      style={{
        display: "inline-grid",
        width: 20,
        height: 20,
        placeItems: "center",
        flexShrink: 0,
      }}
    >
      <MissiveIconSVG ref={ref} {...props} />
    </span>
  );
});
