// Asana 图标组件 - 用于 Asana 项目管理平台相关组件的标识
import React, { forwardRef } from "react";
import SvgAsana from "./asana";

export const AsanaIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
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
        <SvgAsana ref={ref} {...props} />
      </span>
    );
  },
);
