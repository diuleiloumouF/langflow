// Supabase 图标组件 - 用于 Supabase 开源 Firebase 替代方案相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSupabaseIcon from "./SupabaseIcon";

export const SupabaseIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <span
      style={{
        display: "inline-grid",
        width: 22,
        height: 22,
        placeItems: "center",
        flexShrink: 0,
      }}
    >
      <SvgSupabaseIcon ref={ref} {...props} />
    </span>
  );
});
