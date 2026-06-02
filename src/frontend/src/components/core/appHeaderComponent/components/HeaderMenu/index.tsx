import { ChevronsUpDown } from "lucide-react";
import type React from "react";
import ForwardedIconComponent from "@/components/common/genericIconComponent";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/utils/utils";

// 头部菜单容器组件
export const HeaderMenu = ({ children }) => (
  <DropdownMenu>{children}</DropdownMenu>
);

// 头部菜单触发器组件，显示用户头像和展开/折叠图标
export const HeaderMenuToggle = ({ children }) => (
  <DropdownMenuTrigger
    className="inline-flex w-full items-center justify-center rounded-md pl-1 pr-1"
    data-testid="user_menu_button"
    id="user_menu_button"
  >
    <div className="group flex items-center self-center rounded-md">
      <div className="flex h-6 w-10 items-center justify-center rounded-full bg-background transition-colors hover:bg-muted group-hover:bg-muted">
        <div className="relative right-1 z-10">{children}</div>
        <ChevronsUpDown className="relative h-[14px] w-[14px] text-muted-foreground group-hover:text-primary" />
      </div>
    </div>
  </DropdownMenuTrigger>
);

// 头部菜单链接项组件
export const HeaderMenuItemLink = ({
  href = "#",
  children,
  newPage = false,
  icon = "external-link",
}) => (
  <DropdownMenuItem className="cursor-pointer rounded-none p-3 px-4" asChild>
    <a
      href={href}
      className="group flex w-full items-center justify-between"
      {...(newPage ? { rel: "noreferrer", target: "_blank" } : {})}
    >
      {children}
      {icon && (
        <ForwardedIconComponent
          name={icon}
          className="side-bar-button-size h-[18px] w-[18px] opacity-0 group-hover:opacity-100  group-focus-visible:opacity-100"
        />
      )}
    </a>
  </DropdownMenuItem>
);

// 头部菜单按钮项组件
export const HeaderMenuItemButton = ({ icon = "", onClick, children }) => (
  <DropdownMenuItem
    className="group flex cursor-pointer items-center justify-between p-3 px-4"
    onClick={onClick}
  >
    {children}
    {icon && (
      <ForwardedIconComponent
        name={icon}
        className="side-bar-button-size mr-3 h-[18px] w-[18px] opacity-0 transition-all duration-300 group-hover:translate-x-3 group-hover:opacity-100 group-focus-visible:translate-x-3 group-focus-visible:opacity-100"
      />
    )}
  </DropdownMenuItem>
);

// 头部菜单内容组件，支持左对齐和右对齐
export const HeaderMenuItems = ({
  position = "left",
  children,
  classNameSize = "w-[20rem]",
}: React.PropsWithChildren<{
  position?: "left" | "right";
  classNameSize?: string;
}>) => {
  const positionClass = position === "left" ? "left-0" : "right-0";
  return (
    <DropdownMenuContent className={cn(classNameSize, positionClass)}>
      {children}
    </DropdownMenuContent>
  );
};

// 头部菜单分组组件，自动添加分隔线
export const HeaderMenuItemsSection = ({ children }) => (
  <>
    {children}
    <DropdownMenuSeparator className="last:hidden" />
  </>
);

// 头部菜单标题组件
export const HeaderMenuItemsTitle = ({
  subTitle,
  children,
}: React.PropsWithChildren<{ subTitle?: React.ReactNode }>) => (
  <header className="group flex w-full flex-col items-start rounded-md rounded-b-none border px-4 py-3">
    <h3 className="text-base font-semibold">{children}</h3>
    {subTitle ? <h4 className="text-sm font-normal">{subTitle}</h4> : null}
  </header>
);
