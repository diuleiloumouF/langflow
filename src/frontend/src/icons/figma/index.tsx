// Figma 图标组件 - 用于 Figma 协作设计工具相关组件的标识
import React, { forwardRef } from "react";
import FigmaIconSVG from "./figma";

export const FigmaIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
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
        <FigmaIconSVG ref={ref} {...props} />
      </span>
    );
  },
);
