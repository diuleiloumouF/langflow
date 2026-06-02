// PandaDoc 图标组件 - 用于 PandaDoc 电子签名和文档自动化平台相关组件的标识
import React, { forwardRef } from "react";
import PandadocIconSVG from "./pandadoc";

export const PandadocIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <PandadocIconSVG ref={ref} {...props} />;
});
