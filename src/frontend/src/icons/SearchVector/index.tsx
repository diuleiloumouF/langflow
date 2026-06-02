// SearchVector 图标组件 - 用于向量搜索功能相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSearchVectorIcon from "./SearchVectorIcon";

export const SearchVectorIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgSearchVectorIcon ref={ref} {...props} />;
});
