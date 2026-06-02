// Listen Notes 图标组件 - 用于 Listen Notes 播客搜索引擎相关组件的标识
import React, { forwardRef } from "react";
import ListennotesIconSVG from "./listennotes";

export const ListennotesIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <ListennotesIconSVG ref={ref} {...props} />;
});
