// FreezeAll 图标组件 - 用于冻结所有节点状态操作的标识
import type React from "react";
import { forwardRef } from "react";
import SvgFreezeAll from "./freezeAll";

export const freezeAllIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{ className?: string }>
>((props, ref) => {
  return <SvgFreezeAll ref={ref} {...props} />;
});
