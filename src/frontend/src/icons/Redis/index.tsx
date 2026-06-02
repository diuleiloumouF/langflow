// Redis 图标组件 - 用于 Redis 内存数据库相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import { SvgRedis } from "./Redis";

export const RedisIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgRedis ref={ref} {...props} />;
  },
);
