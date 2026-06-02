// Couchbase 图标组件 - 用于 Couchbase NoSQL 数据库相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgCouchbaseIcon from "./Couchbase";

export const CouchbaseIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgCouchbaseIcon ref={ref} {...props} />;
});
