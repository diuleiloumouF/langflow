// Chroma 图标组件 - 用于 Chroma 向量数据库相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgChroma from "./Chroma";

export const ChromaIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgChroma ref={ref} {...props} />;
});
