import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Cross2Icon } from "@radix-ui/react-icons";
import * as React from "react";
import DialogContentWithouFixed from "@/customization/components/custom-dialog-content-without-fixed";
import { dialogClass } from "@/customization/utils/dialog-class";
import { cn } from "../../utils/utils";
import ShadTooltip from "../common/shadTooltipComponent";

// 对话框根组件
const Dialog = DialogPrimitive.Root;

// 对话框触发器组件
const DialogTrigger = DialogPrimitive.Trigger;

// 对话框 Portal 组件，将内容渲染到 DOM 树外层
const DialogPortal = ({
  children,
  ...props
}: DialogPrimitive.DialogPortalProps) => (
  <DialogPrimitive.Portal {...props}>
    <div className="nopan nodelete nodrag noflow fixed inset-0 z-50 flex items-center justify-center">
      {children}
    </div>
  </DialogPrimitive.Portal>
);
DialogPortal.displayName = DialogPrimitive.Portal.displayName;

// 对话框遮罩层组件
const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(dialogClass.dialogContent, className)}
    {...props}
  />
));
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName;

// 可视隐藏组件，用于辅助功能（屏幕阅读器可访问但视觉上隐藏）
// Create a VisuallyHidden component for accessibility
const VisuallyHidden = React.forwardRef<
  HTMLSpanElement,
  React.HTMLAttributes<HTMLSpanElement>
>(({ children, ...props }, ref) => (
  <span
    ref={ref}
    className="absolute h-px w-px overflow-hidden whitespace-nowrap border-0 p-0"
    style={{ clip: "rect(0 0 0 0)", clipPath: "inset(50%)" }}
    {...props}
  >
    {children}
  </span>
));
VisuallyHidden.displayName = "VisuallyHidden";

// 对话框内容组件，包含遮罩层、内容区域和关闭按钮
const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> & {
    hideTitle?: boolean;
    closeButtonClassName?: string;
    overlayClassName?: string;
  }
>(
  (
    {
      className,
      children,
      hideTitle = false,
      closeButtonClassName,
      overlayClassName,
      onOpenAutoFocus,
      ...props
    },
    ref,
  ) => {
    // Check if DialogTitle is included in children
    const hasDialogTitle = React.Children.toArray(children).some(
      (child) => React.isValidElement(child) && child.type === DialogTitle,
    );
    const hasDialogDescription = React.Children.toArray(children).some(
      (child) =>
        React.isValidElement(child) && child.type === DialogDescription,
    );

    return (
      <DialogPortal>
        <DialogOverlay className={overlayClassName} />
        <DialogPrimitive.Content
          ref={ref}
          className={cn(
            "fixed z-50 flex w-full max-w-lg flex-col gap-4 rounded-xl border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%]",
            className,
          )}
          onOpenAutoFocus={(e) => {
            if (onOpenAutoFocus) {
              onOpenAutoFocus(e);
            } else {
              e.preventDefault();
            }
          }}
          {...props}
        >
          {!hasDialogTitle && (
            <VisuallyHidden>
              <DialogTitle>Dialog</DialogTitle>
            </VisuallyHidden>
          )}
          {!hasDialogDescription && (
            <VisuallyHidden>
              <DialogDescription />
            </VisuallyHidden>
          )}
          {children}
          <ShadTooltip
            styleClasses="z-50"
            content="Close"
            side="bottom"
            avoidCollisions
          >
            <DialogPrimitive.Close
              className={cn(
                "absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-sm ring-offset-background transition-opacity hover:bg-secondary-hover hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground",
                closeButtonClassName,
              )}
            >
              <Cross2Icon className="h-[18px] w-[18px]" />
              <span className="sr-only">Close</span>
            </DialogPrimitive.Close>
          </ShadTooltip>
        </DialogPrimitive.Content>
      </DialogPortal>
    );
  },
);

// 对话框头部组件
const DialogHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn("flex flex-col space-y-1 text-left", className)}
    {...props}
  />
);
DialogHeader.displayName = "DialogHeader";

// 对话框底部组件
const DialogFooter = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
      className,
    )}
    {...props}
  />
);
DialogFooter.displayName = "DialogFooter";

// 对话框标题组件
const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn(
      "text-lg font-semibold leading-none tracking-tight",
      className,
    )}
    {...props}
  />
));
DialogTitle.displayName = DialogPrimitive.Title.displayName;

// 对话框描述组件
const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
));
DialogDescription.displayName = DialogPrimitive.Description.displayName;

export {
  Dialog,
  DialogContent,
  DialogContentWithouFixed,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  VisuallyHidden,
};
