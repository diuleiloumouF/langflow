// Cloudflare 图标组件 - 用于 Cloudflare CDN 和安全服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgCloudflareIcon from "./Cloudflare";

export const CloudflareIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgCloudflareIcon ref={ref} {...props} />;
});
