import { useEffect, useState } from "react";
import { useHotkeys } from "react-hotkeys-hook";
import { useBlocker, useParams } from "react-router-dom";
import { AssistantPanel } from "@/components/core/assistantPanel";
import { FlowPageSlidingContainerContent } from "@/components/core/playgroundComponent/sliding-container/components/flow-page-sliding-container";
import { SidebarProvider, useSidebar } from "@/components/ui/sidebar";
import {
  SimpleSidebar,
  SimpleSidebarProvider,
} from "@/components/ui/simple-sidebar";
import { useGetFlow } from "@/controllers/API/queries/flows/use-get-flow";
import { useGetTypes } from "@/controllers/API/queries/flows/use-get-types";
import { ENABLE_NEW_SIDEBAR } from "@/customization/feature-flags";
import { useCustomNavigate } from "@/customization/hooks/use-custom-navigate";
import useApplyFlowToCanvas from "@/hooks/flows/use-apply-flow-to-canvas";
import useSaveFlow from "@/hooks/flows/use-save-flow";
import { useIsMobile } from "@/hooks/use-mobile";
import { useWebhookEvents } from "@/hooks/use-webhook-events";
import { SaveChangesModal } from "@/modals/saveChangesModal";
import useAlertStore from "@/stores/alertStore";
import useAssistantManagerStore from "@/stores/assistantManagerStore";
import { usePlaygroundStore } from "@/stores/playgroundStore";
import { useShortcutsStore } from "@/stores/shortcuts";
import { useTypesStore } from "@/stores/typesStore";
import { customStringify } from "@/utils/reactflowUtils";
import { cn } from "@/utils/utils";
import useFlowStore from "../../stores/flowStore";
import useFlowsManagerStore from "../../stores/flowsManagerStore";
import {
  FlowSearchProvider,
  FlowSidebarComponent,
} from "./components/flowSidebarComponent";
import Page from "./components/PageComponent";
import { FlowInsightsContent } from "./components/TraceComponent/FlowInsightsContent";

/**
 * 流程页面主内容区域
 * 根据当前侧边栏的活动区域，显示流程画布或追踪分析内容
 */
function FlowPageMainContent({
  flowId,
  setIsLoading,
}: {
  flowId?: string;
  setIsLoading: (isLoading: boolean) => void;
}): JSX.Element {
  const { activeSection } = useSidebar();
  const showTraces = ENABLE_NEW_SIDEBAR && activeSection === "traces";

  if (showTraces) {
    return (
      <div
        className="flex h-full w-full flex-col overflow-hidden"
        data-testid="flow-insights-embedded"
      >
        <FlowInsightsContent
          flowId={flowId}
          refreshOnMount
          showFlowActivityHeader
        />
      </div>
    );
  }

  return <Page setIsLoading={setIsLoading} />;
}

/**
 * 流程页面主组件
 * 管理流程编辑器的完整生命周期，包括加载流程、保存、自动保存、离开确认等
 * @param view - 是否为只读视图模式
 */
export default function FlowPage({ view }: { view?: boolean }): JSX.Element {
  const types = useTypesStore((state) => state.types);

  useGetTypes({
    enabled: Object.keys(types).length <= 0,
  });

  const setCurrentFlow = useFlowsManagerStore((state) => state.setCurrentFlow);
  const currentFlow = useFlowStore((state) => state.currentFlow);
  const currentSavedFlow = useFlowsManagerStore((state) => state.currentFlow);
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const [isLoading, setIsLoading] = useState(false);

  // 判断流程是否有未保存的更改
  const changesNotSaved =
    customStringify(currentFlow) !== customStringify(currentSavedFlow) &&
    (currentFlow?.data?.nodes?.length ?? 0) > 0;

  const isBuilding = useFlowStore((state) => state.isBuilding);
  const blocker = useBlocker(changesNotSaved || isBuilding);

  const setOnFlowPage = useFlowStore((state) => state.setOnFlowPage);
  const { id } = useParams();
  const navigate = useCustomNavigate();
  const saveFlow = useSaveFlow();

  const flows = useFlowsManagerStore((state) => state.flows);
  const currentFlowId = useFlowsManagerStore((state) => state.currentFlowId);

  const updatedAt = currentSavedFlow?.updated_at;
  const autoSaving = useFlowsManagerStore((state) => state.autoSaving);
  const stopBuilding = useFlowStore((state) => state.stopBuilding);

  const { mutateAsync: getFlow } = useGetFlow();
  const applyFlowToCanvas = useApplyFlowToCanvas();

  // 连接到 Webhook 事件的 SSE 实时反馈
  // Connect to webhook events SSE for real-time feedback
  useWebhookEvents();

  // 处理保存流程操作
  const handleSave = () => {
    let saving = true;
    let proceed = false;
    setTimeout(() => {
      saving = false;
      if (proceed) {
        blocker.proceed && blocker.proceed();
        setSuccessData({
          title: "Flow saved successfully!",
        });
      }
    }, 1200);
    saveFlow().then(() => {
      if (!autoSaving || saving === false) {
        blocker.proceed && blocker.proceed();
        setSuccessData({
          title: "Flow saved successfully!",
        });
      }
      proceed = true;
    });
  };

  // 处理离开流程页面的操作
  const handleExit = () => {
    if (isBuilding) {
      // Do nothing, let the blocker handle it
    } else if (changesNotSaved) {
      if (blocker.proceed) blocker.proceed();
    } else {
      navigate("/all");
    }
  };

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (changesNotSaved || isBuilding) {
        event.preventDefault();
        event.returnValue = ""; // Required for Chrome
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [changesNotSaved, isBuilding]);

  // 设置当前流程标签页，加载流程数据到画布
  // Set flow tab id
  useEffect(() => {
    const awaitgetTypes = async () => {
      if (flows && currentFlowId === "" && Object.keys(types).length > 0) {
        const isAnExistingFlow = flows.find((flow) => flow.id === id);

        if (!isAnExistingFlow) {
          navigate("/all");
          return;
        }

        const isAnExistingFlowId = isAnExistingFlow.id;

        await getFlowToAddToCanvas(isAnExistingFlowId);
      }
    };
    awaitgetTypes();
  }, [id, flows, currentFlowId, types]);

  useEffect(() => {
    setOnFlowPage(true);

    return () => {
      setOnFlowPage(false);
      setCurrentFlow(undefined);
      // Reset playground state when leaving the flow
      setSlidingContainerOpen(false);
      setIsFullscreen(false);
    };
  }, [id]);

  useEffect(() => {
    if (
      blocker.state === "blocked" &&
      autoSaving &&
      changesNotSaved &&
      !isBuilding
    ) {
      handleSave();
    }
  }, [blocker.state, isBuilding]);

  useEffect(() => {
    if (blocker.state === "blocked") {
      if (isBuilding) {
        stopBuilding();
      } else if (!changesNotSaved) {
        blocker.proceed && blocker.proceed();
      }
    }
  }, [blocker.state, isBuilding]);

  // 获取流程数据并应用到画布
  const getFlowToAddToCanvas = async (id: string) => {
    const flow = await getFlow({ id });
    applyFlowToCanvas(flow);
  };

  const isMobile = useIsMobile();
  const isSlidingContainerOpen = usePlaygroundStore((state) => state.isOpen);
  const setSlidingContainerOpen = usePlaygroundStore(
    (state) => state.setIsOpen,
  );
  const isFullscreen = usePlaygroundStore((state) => state.isFullscreen);
  const setIsFullscreen = usePlaygroundStore((state) => state.setIsFullscreen);
  const inputs = useFlowStore((state) => state.inputs);
  const outputs = useFlowStore((state) => state.outputs);

  // AI 助手状态管理
  // Assistant state
  const assistantOpen = useAssistantManagerStore(
    (state) => state.assistantSidebarOpen,
  );
  const setAssistantOpen = useAssistantManagerStore(
    (state) => state.setAssistantSidebarOpen,
  );

  // 使用可配置的快捷键切换 AI 助手（仅在未在输入框中输入时生效）
  // Toggle assistant with configurable shortcut (only when not typing in an input)
  const aiAssistantShortcut = useShortcutsStore((state) => state.aiAssistant);
  useHotkeys(
    aiAssistantShortcut,
    () => setAssistantOpen(!assistantOpen),
    {
      preventDefault: true,
      enableOnFormTags: false,
    },
    [assistantOpen, aiAssistantShortcut],
  );

  // 按 Escape 键关闭 AI 助手
  // Close assistant with Escape
  useHotkeys(
    "escape",
    () => {
      if (assistantOpen) setAssistantOpen(false);
    },
    {
      enableOnFormTags: true,
    },
    [assistantOpen],
  );

  // 当所有聊天组件被移除时，自动关闭 Playground
  // Auto-close playground when all chat components are removed
  useEffect(() => {
    const hasChatInput = inputs.some((input) => input.type === "ChatInput");
    const hasChatOutput = outputs.some(
      (output) => output.type === "ChatOutput",
    );

    if (isSlidingContainerOpen && !hasChatInput && !hasChatOutput) {
      setSlidingContainerOpen(false);
      setIsFullscreen(false);
    }
  }, [
    inputs,
    outputs,
    isSlidingContainerOpen,
    setSlidingContainerOpen,
    setIsFullscreen,
  ]);

  return (
    <>
      {/* Assistant Panel - single instance that handles both modes internally */}
      <AssistantPanel
        isOpen={assistantOpen}
        onClose={() => setAssistantOpen(false)}
      />

      <div className="flow-page-positioning">
        {currentFlow && (
          <div className="flex h-full overflow-hidden">
            {/* Main content + Playground Sidebar (right) */}
            <SimpleSidebarProvider
              width="326px"
              minWidth={0.15}
              maxWidth={0.6}
              open={isSlidingContainerOpen}
              onOpenChange={(open) => {
                const wasOpen = isSlidingContainerOpen;
                setSlidingContainerOpen(open);
                if (open && !wasOpen) {
                  setIsFullscreen(true);
                }
              }}
              fullscreen={isFullscreen}
              onMaxWidth={() => {
                setIsFullscreen(true);
                setSlidingContainerOpen(true);
              }}
            >
              <SidebarProvider
                width="17.5rem"
                defaultOpen={!isMobile}
                segmentedSidebar={ENABLE_NEW_SIDEBAR}
              >
                <FlowSearchProvider>
                  {/* FlowSidebarComponent - stays in place */}
                  {!view && <FlowSidebarComponent isLoading={isLoading} />}

                  <main
                    className={cn(
                      "flex flex-1 min-w-0 overflow-hidden transition-all duration-300",
                      isSlidingContainerOpen &&
                        !isFullscreen &&
                        "rounded-xl m-2 mr-0",
                    )}
                  >
                    <div className="h-full w-full">
                      <FlowPageMainContent
                        flowId={id}
                        setIsLoading={setIsLoading}
                      />
                    </div>
                  </main>
                </FlowSearchProvider>
              </SidebarProvider>
              <SimpleSidebar resizable={!isFullscreen} className="h-full">
                <FlowPageSlidingContainerContent
                  isFullscreen={isFullscreen}
                  setIsFullscreen={setIsFullscreen}
                />
              </SimpleSidebar>
            </SimpleSidebarProvider>
          </div>
        )}
      </div>
      {blocker.state === "blocked" && (
        <>
          {!isBuilding && currentSavedFlow && (
            <SaveChangesModal
              onSave={handleSave}
              onCancel={() => blocker.reset?.()}
              onProceed={handleExit}
              flowName={currentSavedFlow.name}
              lastSaved={
                updatedAt
                  ? new Date(updatedAt).toLocaleString("en-US", {
                      hour: "numeric",
                      minute: "numeric",
                      second: "numeric",
                      month: "numeric",
                      day: "numeric",
                    })
                  : undefined
              }
              autoSave={autoSaving}
            />
          )}
        </>
      )}
    </>
  );
}
