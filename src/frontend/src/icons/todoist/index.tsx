// Todoist 图标组件 - 用于 Todoist 任务管理应用相关组件的标识
import React, { forwardRef } from "react";
import TodoistIconSVG from "./todoist";

export const TodoistIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return (
    <span
      style={{
        display: "inline-grid",
        width: 22,
        height: 22,
        placeItems: "center",
        flexShrink: 0,
      }}
    >
      <TodoistIconSVG ref={ref} {...props} />
    </span>
  );
});
