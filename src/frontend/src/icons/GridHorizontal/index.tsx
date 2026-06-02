// GridHorizontal 图标组件 - 用于水平网格布局相关组件的标识
import { forwardRef } from "react";
import SVGGridHorizontalIcon from "./GridHorizontalIcon";

export const GridHorizontalIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SVGGridHorizontalIcon ref={ref} {...props} />;
});
