// GitBook 图标组件 - 用于 GitBook 文档平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgGitbookSvgrepoCom from "./GitbookSvgrepoCom";

export const GitBookIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgGitbookSvgrepoCom ref={ref} {...props} />;
});
