// Fireflies 图标组件 - 用于 Fireflies AI 会议记录服务相关组件的标识
import React, { forwardRef } from "react";
import FirefliesIconSVG from "./fireflies.jsx";

export const FirefliesIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <span
      style={{
        display: "inline-grid",
        width: 22,
        height: 22,
        placeItems: "center",
        flexShrink: 0,
      }}
    >
      <FirefliesIconSVG ref={ref} {...props} />
    </span>
  );
});
