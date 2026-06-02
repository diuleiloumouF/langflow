// Wikipedia 图标组件 - 用于 Wikipedia 百科全书服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgWikipedia from "./Wikipedia";

export const WikipediaIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgWikipedia ref={ref} {...props} />;
});
