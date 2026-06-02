// JigsawStack 图标组件 - 用于 JigsawStack AI 工具栈服务相关组件的标识
import React, { forwardRef } from "react";
import { useDarkStore } from "@/stores/darkStore";
import JigsawStackIconSVG from "./JigsawStackIcon";

export const JigsawStackIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <JigsawStackIconSVG ref={ref} {...props} />;
});
