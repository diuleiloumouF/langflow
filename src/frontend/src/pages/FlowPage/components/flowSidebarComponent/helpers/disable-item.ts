import type { UniqueInputsComponents } from "../types";
import {
  CHAT_INPUT_COMPONENT,
  EXCLUSIVITY_RULES,
  WEBHOOK_COMPONENT,
} from "./constants";

/**
 * 判断组件项是否应被禁用
 * 根据唯一输入组件的排他性规则，检查组件是否可以添加到画布
 */
export const disableItem = (
  SBItemName: string,
  uniqueInputsComponents: UniqueInputsComponents,
) => {
  // Check if component already exists
  if (SBItemName === CHAT_INPUT_COMPONENT && uniqueInputsComponents.chatInput) {
    return true;
  }
  if (SBItemName === WEBHOOK_COMPONENT && uniqueInputsComponents.webhookInput) {
    return true;
  }

  // Check exclusivity rules
  const exclusiveComponents = EXCLUSIVITY_RULES[SBItemName];
  if (exclusiveComponents) {
    for (const exclusiveComponent of exclusiveComponents) {
      if (
        exclusiveComponent === CHAT_INPUT_COMPONENT &&
        uniqueInputsComponents.chatInput
      ) {
        return true;
      }
      if (
        exclusiveComponent === WEBHOOK_COMPONENT &&
        uniqueInputsComponents.webhookInput
      ) {
        return true;
      }
    }
  }

  return false;
};
