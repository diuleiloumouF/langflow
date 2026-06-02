import type { ConnectionLineComponentProps } from "@xyflow/react";
import useFlowStore from "@/stores/flowStore";

/**
 * 连接线组件
 * 在用户拖拽连接时绘制贝塞尔曲线连接线和目标圆点
 * 连接线颜色根据拖拽目标的数据类型自动适配
 */
const ConnectionLineComponent = ({
  fromX,
  fromY,
  toX,
  toY,
  connectionLineStyle = {},
}: ConnectionLineComponentProps): JSX.Element => {
  const handleDragging = useFlowStore((state) => state.handleDragging);
  const color = handleDragging?.color;
  const accentColor = `hsl(var(--datatype-${color}))`;

  return (
    <g>
      <path
        fill="none"
        // ! Replace hash # colors here
        strokeWidth={2}
        className={`animated`}
        style={{
          stroke: handleDragging ? accentColor : "",
          ...connectionLineStyle,
        }}
        d={`M${fromX},${fromY} C ${fromX} ${toY} ${fromX} ${toY} ${toX},${toY}`}
      />
      <circle
        cx={toX}
        cy={toY}
        fill="#fff"
        r={5}
        stroke={accentColor}
        className=""
        strokeWidth={1.5}
      />
    </g>
  );
};

export default ConnectionLineComponent;
