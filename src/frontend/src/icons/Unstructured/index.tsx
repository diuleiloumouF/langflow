// Unstructured 图标组件 - 用于 Unstructured 文档解析服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgUnstructured from "./Unstructured";

export const UnstructuredIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgUnstructured ref={ref} {...props} />;
});
