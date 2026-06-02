// Facebook Messenger 图标组件 - 用于 Facebook Messenger 即时通讯服务相关组件的标识
import type React from "react";
import { forwardRef } from "react";
import SvgFacebookMessengerLogo2020 from "./FacebookMessengerLogo2020";

export const FBIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgFacebookMessengerLogo2020 ref={ref} {...props} />;
  },
);
