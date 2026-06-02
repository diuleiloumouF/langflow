// SearchLexical 图标组件 - 用于词法搜索功能相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgSearchLexicalIcon from "./SearchLexicalIcon";

export const SearchLexicalIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgSearchLexicalIcon ref={ref} {...props} />;
});
