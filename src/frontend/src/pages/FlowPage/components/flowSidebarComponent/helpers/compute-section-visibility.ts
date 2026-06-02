/** 区块可见性计算的输入参数 */
export interface SectionVisibilityInput {
  enableNewSidebar: boolean;
  activeSection: string;
  hasSearchInput: boolean;
  hasCoreComponents: boolean;
  hasMcpComponents: boolean;
  hasBundleItems: boolean;
}

/** 区块可见性计算的输出结果 */
export interface SectionVisibilityOutput {
  showComponents: boolean;
  showBundles: boolean;
  showMcp: boolean;
  isMcpTabActive: boolean;
}

/**
 * 计算侧边栏各区块的可见性
 * 根据侧边栏模式、活动区域和数据状态决定显示哪些区块
 */
export function computeSectionVisibility(
  input: SectionVisibilityInput,
): SectionVisibilityOutput {
  const {
    enableNewSidebar,
    activeSection,
    hasSearchInput,
    hasCoreComponents,
    hasMcpComponents,
    hasBundleItems,
  } = input;

  const showComponents =
    (enableNewSidebar &&
      hasCoreComponents &&
      (activeSection === "components" || activeSection === "search")) ||
    (hasSearchInput && hasCoreComponents && enableNewSidebar) ||
    !enableNewSidebar;

  const showBundles =
    (hasBundleItems && enableNewSidebar && activeSection === "bundles") ||
    (hasSearchInput && hasBundleItems && enableNewSidebar) ||
    !enableNewSidebar;

  const showMcp =
    (enableNewSidebar && activeSection === "mcp") ||
    (hasSearchInput && hasMcpComponents && enableNewSidebar);

  const isMcpTabActive = enableNewSidebar && activeSection === "mcp";

  return { showComponents, showBundles, showMcp, isMcpTabActive };
}
