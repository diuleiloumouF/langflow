// Cassandra 图标组件 - 用于 Apache Cassandra 数据库相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import CassandraSVG from "./Cassandra";

export const CassandraIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <CassandraSVG ref={ref} {...props} />;
});
