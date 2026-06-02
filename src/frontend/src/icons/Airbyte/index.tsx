// Airbyte 图标组件 - 用于 Airbyte 数据集成平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgAirbyte from "./Airbyte";

export const AirbyteIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgAirbyte ref={ref} {...props} />;
});
