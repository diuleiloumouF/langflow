// Attio 图标组件 - 用于 Attio 智能 CRM 平台相关组件的标识
import React, { forwardRef } from "react";
import SvgAttio from "./attio";

export const AttioIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
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
        <SvgAttio ref={ref} {...props} />
      </span>
    );
  },
);
