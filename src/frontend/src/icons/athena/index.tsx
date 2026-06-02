// Athena 图标组件 - 用于 Amazon Athena 交互式查询服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
//@ts-ignore
import { AthenaComponent } from "./athena";

export const AthenaIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{ className?: string }>
>((props, ref) => {
  return <AthenaComponent ref={ref} {...props} />;
});
