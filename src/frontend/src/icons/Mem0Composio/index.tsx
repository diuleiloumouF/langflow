// Mem0 Composio 图标组件 - 用于 Mem0 通过 Composio 集成的记忆管理服务相关组件的标识
import React, { forwardRef } from "react";
import SvgMem from "./SvgMem";

export const Mem0IconComposio = forwardRef<
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
      <SvgMem className="icon" ref={ref} {...props} />
    </span>
  );
});
