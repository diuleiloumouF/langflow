// MongoDB 图标组件 - 用于 MongoDB NoSQL 数据库相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgMongodbIcon from "./MongodbIcon";

export const MongoDBIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgMongodbIcon ref={ref} {...props} />;
});
