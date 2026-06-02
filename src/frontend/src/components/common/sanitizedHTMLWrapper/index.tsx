import DOMPurify from "dompurify";
import { forwardRef } from "react";
import { cn } from "@/utils/utils";
import type { SanitizedHTMLWrapperType } from "../../../types/components";

/**
 * HTML 消毒包装器组件
 * 使用 DOMPurify 对 HTML 内容进行消毒处理，防止 XSS 攻击。
 * 支持抑制 contentEditable 警告。
 */
const SanitizedHTMLWrapper = forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLHeadingElement> & SanitizedHTMLWrapperType
>(({ content, suppressWarning = false, ...props }, ref) => {
  const sanitizedHTML = DOMPurify.sanitize(content);

  return (
    <div
      ref={ref}
      data-testid="edit-prompt-sanitized"
      dangerouslySetInnerHTML={{ __html: sanitizedHTML }}
      suppressContentEditableWarning={suppressWarning}
      {...props}
      className={cn("m-1 w-full", props.className)}
    />
  );
});

SanitizedHTMLWrapper.displayName = "SanitizedHTMLWrapper";

export default SanitizedHTMLWrapper;
