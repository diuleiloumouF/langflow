// Excel 图标组件 - 用于 Microsoft Excel 电子表格相关组件的标识
import React, { forwardRef } from "react";
import ExcelIconSVG from "./excel";

export const ExcelIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <ExcelIconSVG ref={ref} {...props} />;
  },
);
