// ElevenLabs 图标组件 - 用于 ElevenLabs AI 语音合成服务相关组件的标识
import React, { forwardRef } from "react";
import ElevenlabsIconSVG from "./elevenlabs";

export const ElevenlabsIcon = forwardRef<
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
      <ElevenlabsIconSVG ref={ref} {...props} />
    </span>
  );
});
