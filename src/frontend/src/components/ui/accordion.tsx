"use client";

import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDownIcon } from "@radix-ui/react-icons";
import * as React from "react";
import { cn } from "../../utils/utils";
import ShadTooltip from "../common/shadTooltipComponent";

// 手风琴根组件，基于 Radix UI Accordion 原语
const Accordion = AccordionPrimitive.Root;

// 手风琴面板项组件
const AccordionItem = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Item>
>(({ className, ...props }, ref) => (
  <AccordionPrimitive.Item
    ref={ref}
    className={cn("border-b", className)}
    {...props}
  />
));
AccordionItem.displayName = "AccordionItem";

// 手风琴触发器组件，点击展开/折叠面板
const AccordionTrigger = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Trigger>
>(({ className, children, disabled, ...props }, ref) => (
  <AccordionPrimitive.Header className="flex">
    <AccordionPrimitive.Trigger
      disabled={disabled}
      asChild
      ref={ref}
      {...props}
    >
      <div
        className={cn(
          "flex flex-1 cursor-pointer items-center justify-between py-4 text-sm font-medium transition-all [&[data-state=open]>svg]:rotate-180",
          className,
        )}
      >
        {children}
        <ShadTooltip
          styleClasses="z-50"
          content={disabled ? "Empty" : "Open"}
          side="top"
        >
          <ChevronDownIcon
            className={cn(
              "h-4 w-4 font-bold transition-transform duration-200",
              disabled ? "text-muted-foreground" : "text-primary",
            )}
          />
        </ShadTooltip>
      </div>
    </AccordionPrimitive.Trigger>
  </AccordionPrimitive.Header>
));
AccordionTrigger.displayName = AccordionPrimitive.Trigger.displayName;

// 手风琴内容组件，包含折叠/展开动画
const AccordionContent = React.forwardRef<
  React.ElementRef<typeof AccordionPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof AccordionPrimitive.Content>
>(({ className, children, ...props }, ref) => (
  <AccordionPrimitive.Content
    ref={ref}
    className={cn(
      "data-[state=closed]:animate-accordion-up data-[state=open]:animate-accordion-down overflow-hidden text-sm",
      className,
    )}
    {...props}
  >
    <div className="pb-4 pt-0">{children}</div>
  </AccordionPrimitive.Content>
));
AccordionContent.displayName = AccordionPrimitive.Content.displayName;

export { Accordion, AccordionContent, AccordionItem, AccordionTrigger };
