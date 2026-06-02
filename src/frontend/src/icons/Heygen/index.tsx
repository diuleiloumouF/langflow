// Heygen 图标组件 - 用于 Heygen AI 视频生成服务相关组件的标识
import React, { forwardRef } from "react";
import HeygenIconSVG from "./heygen";

export const HeygenIcon = forwardRef<
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
      <HeygenIconSVG ref={ref} {...props} />
    </span>
  );
});
