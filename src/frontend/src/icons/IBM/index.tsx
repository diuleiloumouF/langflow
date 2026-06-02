// IBM 图标组件集合 - 用于 IBM 及其 Watsonx AI 服务相关组件的标识
// WatsonxAiIcon: IBM Watsonx AI 图标
import React, { forwardRef } from "react";
import SvgIBM from "./ibm/IBM";
import SvgWatsonxAI from "./watsonx/WatsonxAI";
import SvgWatsonxOrchestrate from "./watsonx/WatsonxOrchestrate";

export const WatsonxAiIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgWatsonxAI ref={ref} {...props} />;
});

// WatsonxOrchestrateIcon: IBM Watsonx Orchestrate 智能体编排图标
export const WatsonxOrchestrateIcon = forwardRef<
  SVGSVGElement,
  React.PropsWithChildren<{}>
>((props, ref) => {
  return <SvgWatsonxOrchestrate ref={ref} {...props} />;
});

// IBMIcon: IBM 品牌图标
export const IBMIcon = forwardRef<SVGSVGElement, React.PropsWithChildren<{}>>(
  (props, ref) => {
    return <SvgIBM ref={ref} {...props} />;
  },
);
