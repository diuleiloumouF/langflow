// Cursor 图标组件 - 用于 Cursor 代码编辑器相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import CursorSVG from "./Cursor";

export const CursorIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <CursorSVG ref={ref} {...props} />;
});
