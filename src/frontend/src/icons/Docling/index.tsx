// Docling 图标组件 - 用于 Docling 文档处理服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgDocling from "./Docling";

export const DoclingIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgDocling ref={ref} {...props} />;
});
