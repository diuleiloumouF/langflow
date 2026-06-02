// Calendly 图标组件 - 用于 Calendly 在线预约调度平台相关组件的标识
import React, { forwardRef } from "react";
import CalendlyIconSVG from "./calendly";

export const CalendlyIcon = forwardRef<
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
      <CalendlyIconSVG ref={ref} {...props} />
    </span>
  );
});
