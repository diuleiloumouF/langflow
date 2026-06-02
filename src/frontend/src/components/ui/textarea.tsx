import * as React from "react";
import { cn } from "../../utils/utils";

/**
 * 文本域属性类型
 * 扩展原生 HTML textarea 属性
 */
export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  password?: boolean; // 是否为密码模式
  editNode?: boolean; // 是否为节点编辑模式
}

// 文本域组件，支持密码模式和节点编辑模式
const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, password, editNode, ...props }, ref) => {
    return (
      <div className="h-full w-full">
        <textarea
          data-testid="textarea"
          className={cn(
            "nopan nodelete nodrag noflow textarea-primary nowheel",
            className,
            password ? "password" : "",
          )}
          ref={ref}
          {...props}
          value={props.value as string}
          onChange={props.onChange}
        />
      </div>
    );
  },
);

Textarea.displayName = "Textarea";

export { Textarea };
