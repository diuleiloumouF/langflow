// Notion 图标组件 - 用于 Notion 协作办公平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgNotionLogo from "./NotionLogo";

export const NotionIcon = forwardRef<
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
      <SvgNotionLogo ref={ref} {...props} />
    </span>
  );
});
