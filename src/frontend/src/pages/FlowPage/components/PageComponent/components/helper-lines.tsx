import { useViewport } from "@xyflow/react";
import { HelperLinesState } from "../helpers/helper-lines";

/** 辅助线组件的属性定义 */
interface HelperLinesProps {
  helperLines: HelperLinesState;
}

/**
 * 辅助线组件
 * 在画布上渲染水平和垂直对齐辅助线，帮助用户精确对齐节点
 */
export default function HelperLines({ helperLines }: HelperLinesProps) {
  const { x: viewportX, y: viewportY, zoom } = useViewport();

  if (!helperLines.horizontal && !helperLines.vertical) {
    return null;
  }

  return (
    <svg className="helper-lines">
      {helperLines.horizontal && (
        <line
          x1={0}
          y1={helperLines.horizontal.position * zoom + viewportY}
          x2="100%"
          y2={helperLines.horizontal.position * zoom + viewportY}
          className="helper-line horizontal"
        />
      )}
      {helperLines.vertical && (
        <line
          x1={helperLines.vertical.position * zoom + viewportX}
          y1={0}
          x2={helperLines.vertical.position * zoom + viewportX}
          y2="100%"
          className="helper-line vertical"
        />
      )}
    </svg>
  );
}
