// PostgreSQL 图标组件 - 用于 PostgreSQL 关系型数据库相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgPostgres from "./Postgres";

export const PostgresIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgPostgres ref={ref} {...props} />;
});
