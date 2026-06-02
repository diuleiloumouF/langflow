// Airtable 图标组件 - 用于 Airtable 在线数据库平台相关组件的标识
import React, { forwardRef } from "react";
import AirtableIconSVG from "./airtable";

export const AirtableIcon = forwardRef<
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
      <AirtableIconSVG ref={ref} {...props} />
    </span>
  );
});
