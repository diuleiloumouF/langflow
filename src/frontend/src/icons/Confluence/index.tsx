// Confluence 图标组件 - 用于 Atlassian Confluence 知识库相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgConfluence from "./Confluence";

export const ConfluenceIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgConfluence ref={ref} {...props} />;
});
