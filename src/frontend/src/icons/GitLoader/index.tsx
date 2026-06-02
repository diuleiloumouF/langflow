// GitLoader 图标组件 - 用于 Git 加载状态指示器相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgGitLoader from "./GitLoader";

export const GitLoaderIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgGitLoader ref={ref} {...props} />;
});
