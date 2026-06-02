// SearchAPI 图标组件 - 用于 SearchAPI 搜索接口服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSearchApi from "./SearchAPI";

export const SearchAPIIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgSearchApi ref={ref} {...props} />;
});
