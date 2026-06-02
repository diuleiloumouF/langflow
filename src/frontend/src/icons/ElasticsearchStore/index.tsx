// Elasticsearch 图标组件 - 用于 Elasticsearch 搜索引擎相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgElasticsearchLogo from "./ElasticsearchLogo";

export const ElasticsearchIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgElasticsearchLogo ref={ref} {...props} />;
});
