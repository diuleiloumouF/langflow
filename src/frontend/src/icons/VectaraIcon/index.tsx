// Vectara 图标组件 - 用于 Vectara 语义搜索和 RAG 服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgVectara from "./Vectara";

export const VectaraIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgVectara className="icon" ref={ref} {...props} />;
});
