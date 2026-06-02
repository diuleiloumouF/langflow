// SambaNova 图标组件 - 用于 SambaNova AI 芯片和模型服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSambaNovaLogo from "./SambaNovaLogo";

export const SambaNovaIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgSambaNovaLogo ref={ref} {...props} />;
});
