import ForwardedIconComponent from "@/components/common/genericIconComponent";

interface ConnectionItemProps {
  name: string;
}

/**
 * 连接项组件
 * 显示单个连接的名称和图标
 */
export default function ConnectionItem({ name }: ConnectionItemProps) {
  return (
    <div className="flex items-center gap-2">
      <ForwardedIconComponent
        name="Plug"
        className="h-3 w-3 shrink-0 text-muted-foreground"
      />
      <span className="text-xs text-muted-foreground">{name}</span>
    </div>
  );
}
