import { memo } from "react";
import { ForwardedIconComponent } from "@/components/common/genericIconComponent";
import ShadTooltip from "@/components/common/shadTooltipComponent";
import { Button } from "@/components/ui/button";
import { cn } from "@/utils/utils";
import ShortcutDisplay from "../shortcutDisplay";

/**
 * 工具栏按钮组件
 * 显示单个操作按钮，支持图标、标签和快捷键提示
 */
export const ToolbarButton = memo(
  ({
    onClick,
    icon,
    label,
    shortcut,
    className,
    dataTestId,
  }: {
    onClick: () => void;
    icon: string;
    label?: string;
    shortcut?: any;
    className?: string;
    dataTestId?: string;
  }) => (
    <ShadTooltip
      content={<ShortcutDisplay {...shortcut} />}
      side="top"
      avoidCollisions={true}
    >
      <Button
        className={cn("node-toolbar-buttons", className)}
        variant="ghost"
        onClick={onClick}
        size="node-toolbar"
        data-testid={dataTestId}
      >
        <ForwardedIconComponent name={icon} className="h-4 w-4" />
        {label && <span className="text-mmd font-medium">{label}</span>}
      </Button>
    </ShadTooltip>
  ),
);
