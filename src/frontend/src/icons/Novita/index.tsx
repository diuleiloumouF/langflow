// Novita 图标组件 - 用于 Novita AI 模型服务相关组件的标识
import React, { forwardRef } from "react";
import SvgNovita from "./novita";

export const NovitaIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgNovita ref={ref} {...props} />;
});
