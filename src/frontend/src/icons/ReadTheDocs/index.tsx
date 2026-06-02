// Read the Docs 图标组件 - 用于 Read the Docs 文档托管平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgReadthedocsioIcon from "./ReadthedocsioIcon";

export const ReadTheDocsIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgReadthedocsioIcon ref={ref} {...props} />;
});
