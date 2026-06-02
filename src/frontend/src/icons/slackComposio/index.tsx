// Slack Composio 图标组件 - 用于 Slack 通过 Composio 集成的相关组件的标识
import React, { forwardRef } from "react";
import SlackIconSVG from "./slack";

export const SlackIcons = forwardRef<
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
      <SlackIconSVG ref={ref} {...props} />
    </span>
  );
});
