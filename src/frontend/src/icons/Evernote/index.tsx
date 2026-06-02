// Evernote 图标组件 - 用于 Evernote 印象笔记服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgEvernoteIcon from "./EvernoteIcon";

export const EvernoteIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgEvernoteIcon ref={ref} {...props} />;
});
