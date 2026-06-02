// SearchHybrid 图标组件 - 用于混合搜索功能相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSearchHybridIcon from "./SearchHybridIcon";

export const SearchHybridIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgSearchHybridIcon ref={ref} {...props} />;
});
