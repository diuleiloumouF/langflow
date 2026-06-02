// Home Assistant 图标组件 - 用于 Home Assistant 智能家居平台相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgHomeAssistant from "./HomeAssistant";

export const HomeAssistantIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgHomeAssistant ref={ref} {...props} />;
});
