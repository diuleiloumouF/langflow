import { useState } from "react";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import type { AccordionComponentType } from "@/types/components";
import { cn } from "@/utils/utils";

/**
 * 手风琴组件
 * 基于 shadcn/ui Accordion 封装的可折叠面板组件。
 * 支持禁用状态、默认展开、侧边栏样式等配置。
 */
export default function AccordionComponent({
  trigger,
  children,
  disabled,
  open = [],
  keyValue,
  sideBar,
}: AccordionComponentType): JSX.Element {
  // 手风琴的展开状态，存储当前展开项的 key
  const [value, setValue] = useState(
    open.length === 0 ? "" : getOpenAccordion(),
  );

  // 根据 open 数组和当前 keyValue 判断是否应该默认展开
  function getOpenAccordion(): string {
    let value = "";
    open.forEach((el) => {
      if (el == keyValue) {
        value = keyValue;
      }
    });
    return value;
  }

  function handleClick(): void {
    if (!disabled) {
      value === "" ? setValue(keyValue!) : setValue("");
    }
  }

  return (
    <>
      <Accordion
        type="single"
        className="w-full"
        value={value}
        onValueChange={!disabled ? setValue : () => {}}
      >
        <AccordionItem value={keyValue!} className="border-b">
          <AccordionTrigger
            onClick={() => {
              handleClick();
            }}
            disabled={disabled}
            className={cn(
              sideBar ? "w-full bg-muted px-[0.75rem] py-[0.5rem]" : "ml-3",
              disabled ? "cursor-not-allowed" : "cursor-pointer",
            )}
          >
            {trigger}
          </AccordionTrigger>
          <AccordionContent>
            <div className="AccordionContent flex flex-col">{children}</div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </>
  );
}
