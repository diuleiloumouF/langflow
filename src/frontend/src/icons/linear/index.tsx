// Linear 图标组件 - 用于 Linear 项目管理工具相关组件的标识
import React, { forwardRef } from "react";
import LinearIconSVG from "./linear";

export const LinearIcon = forwardRef<
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
      <LinearIconSVG ref={ref} {...props} />
    </span>
  );
});
