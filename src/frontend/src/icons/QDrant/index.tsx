// Qdrant 图标组件 - 用于 Qdrant 向量数据库相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgQDrant from "./QDrant";

export const QDrantIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgQDrant ref={ref} {...props} />;
});
