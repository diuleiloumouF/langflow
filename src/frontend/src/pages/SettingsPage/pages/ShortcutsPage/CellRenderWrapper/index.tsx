import type { CustomCellRendererProps } from "ag-grid-react";
import RenderIcons from "@/components/common/renderIconComponent";

/**
 * 快捷键单元格渲染组件
 * 将快捷键字符串解析为可视化的按键图标
 */
export default function CellRenderShortcuts(params: CustomCellRendererProps) {
  const shortcut = params.value;
  const splitShortcut = shortcut?.split("+");
  return <RenderIcons filteredShortcut={splitShortcut} tableRender />;
}
