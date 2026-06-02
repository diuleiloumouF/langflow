import { useGetMessagesQuery } from "@/controllers/API/queries/messages";
import SessionView from "@/modals/IOModal/components/session-view";
import HeaderMessagesComponent from "./components/headerMessages";

/**
 * 消息页面组件
 * 显示流程运行的消息历史记录
 */
export default function MessagesPage() {
  useGetMessagesQuery({ mode: "union" });

  return (
    <div className="flex h-full w-full flex-col justify-between gap-6">
      <HeaderMessagesComponent />
      <div className="flex h-full w-full flex-col justify-between">
        <SessionView />
      </div>
    </div>
  );
}
