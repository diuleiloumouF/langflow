// Klaviyo 图标组件 - 用于 Klaviyo 营销自动化平台相关组件的标识
import React, { forwardRef } from "react";
import SvgKlaviyo from "./klaviyo";

export const KlaviyoIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <span
      style={{
        display: "inline-grid",
        width: 20,
        height: 20,
        placeItems: "center",
        flexShrink: 0,
      }}
    >
      <SvgKlaviyo ref={ref} {...props} />
    </span>
  );
});
