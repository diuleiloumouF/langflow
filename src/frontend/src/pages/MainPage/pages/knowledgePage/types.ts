import type { KnowledgeBaseInfo } from "@/controllers/API/queries/knowledge-bases/use-get-knowledge-bases";

/** 知识库标签页的属性定义 */
export interface KnowledgeBasesTabProps {
  quickFilterText: string;
  setQuickFilterText: (text: string) => void;
  selectedFiles: KnowledgeBaseInfo[];
  setSelectedFiles: (files: KnowledgeBaseInfo[]) => void;
  quantitySelected: number;
  setQuantitySelected: (quantity: number) => void;
  isShiftPressed: boolean;
  onRowClick?: (knowledgeBase: KnowledgeBaseInfo) => void;
}
