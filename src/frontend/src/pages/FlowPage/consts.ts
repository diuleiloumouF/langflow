import { DefaultEdge } from "@/CustomEdges";
import GenericNode from "@/CustomNodes/GenericNode";
import NoteNode from "@/CustomNodes/NoteNode";

// 流程画布使用的 ReactFlow 节点/边类型注册表
// Shared ReactFlow node/edge type registrations used by the main canvas
// (PageComponent).
/** 流程画布支持的节点类型映射 */
export const nodeTypes = {
  genericNode: GenericNode,
  noteNode: NoteNode,
};

/** 流程画布支持的边类型映射 */
export const edgeTypes = {
  default: DefaultEdge,
};
