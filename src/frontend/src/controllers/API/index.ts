import type { Edge, Node, ReactFlowJsonObject } from "@xyflow/react";
import axios, { type AxiosRequestConfig, type AxiosResponse } from "axios";
import {
  customGetAppVersions,
  customGetLatestVersion,
} from "@/customization/utils/custom-get-app-latest-version";
import { getBaseUrl } from "@/customization/utils/urls";
/**
 * API 控制器入口模块
 * 导出所有与后端 API 交互的函数
 */
import { api } from "../../controllers/API/api";
import type {
  VertexBuildTypeAPI,
  VerticesOrderTypeAPI,
} from "../../types/api/index";
import type { FlowStyleType, FlowType } from "../../types/flow";
import type { StoreComponentResponse } from "../../types/store";

// GitHub API 基础 URL
const GITHUB_API_URL = "https://api.github.com";
// Discord 邀请链接 API URL
const DISCORD_API_URL =
  "https://discord.com/api/v9/invites/EqksyE2EX9?with_counts=true";

/**
 * 获取 GitHub 仓库的星标数量
 * @param owner - 仓库所有者
 * @param repo - 仓库名称
 * @returns 星标数量，获取失败时返回 null
 */
export async function getRepoStars(owner: string, repo: string) {
  try {
    const response = await axios.get(
      `${GITHUB_API_URL}/repos/${owner}/${repo}`,
    );
    return response?.data.stargazers_count;
  } catch (error) {
    console.error("Error fetching repository data:", error);
    return null;
  }
}

/**
 * 获取 Discord 服务器的成员数量
 * @returns 成员数量，获取失败时返回 null
 */
export async function getDiscordCount() {
  try {
    const response = await axios.get(DISCORD_API_URL);
    return response?.data.approximate_member_count;
  } catch (error) {
    console.error("Error fetching repository data:", error);
    return null;
  }
}

// 获取应用版本信息
export const getAppVersions = customGetAppVersions;
// 获取最新版本信息
export const getLatestVersion = customGetLatestVersion;

/**
 * 创建新的 API 密钥
 * @param name - API 密钥名称
 * @returns 创建的 API 密钥数据
 */
export async function createApiKey(name: string) {
  try {
    const res = await api.post(`${getBaseUrl()}api_key/`, { name });
    if (res.status === 200) {
      return res.data;
    }
  } catch (error) {
    throw error;
  }
}

/**
 * Saves a new flow to the database.
 *
 * @param {FlowType} newFlow - The flow data to save.
 * @returns {Promise<any>} The saved flow data.
 * @throws Will throw an error if saving fails.
 */
export async function saveFlowStore(
  newFlow: {
    name?: string;
    data: ReactFlowJsonObject | null;
    description?: string;
    style?: FlowStyleType;
    is_component?: boolean;
    parent?: string;
    last_tested_version?: string;
  },
  tags: string[],
  publicFlow = false,
): Promise<FlowType> {
  try {
    const response = await api.post(`${getBaseUrl()}store/components/`, {
      name: newFlow.name,
      data: newFlow.data,
      description: newFlow.description,
      is_component: newFlow.is_component,
      parent: newFlow.parent,
      tags: tags,
      private: !publicFlow,
      status: publicFlow ? "Public" : "Private",
      last_tested_version: newFlow.last_tested_version,
    });

    if (response.status !== 201) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response?.data;
  } catch (error) {
    console.error(error);
    throw error;
  }
}

/**
 * 从组件商店获取组件列表
 * @param options - 查询参数，包括分页、排序、标签过滤等
 * @returns 组件列表数据
 */
export async function getStoreComponents({
  component_id = null,
  page = 1,
  limit = 9999999,
  is_component = null,
  sort = "-count(liked_by)",
  tags = [],
  liked = null,
  isPrivate = null,
  search = null,
  filterByUser = null,
  fields = null,
}: {
  component_id?: string | null;
  page?: number;
  limit?: number;
  is_component?: boolean | null;
  sort?: string;
  tags?: string[] | null;
  liked?: boolean | null;
  isPrivate?: boolean | null;
  search?: string | null;
  filterByUser?: boolean | null;
  fields?: Array<string> | null;
}): Promise<StoreComponentResponse | undefined> {
  try {
    let url = `${getBaseUrl()}store/components/`;
    const queryParams: any = [];
    if (component_id !== undefined && component_id !== null) {
      queryParams.push(`component_id=${component_id}`);
    }
    if (search !== undefined && search !== null) {
      queryParams.push(`search=${search}`);
    }
    if (isPrivate !== undefined && isPrivate !== null) {
      queryParams.push(`private=${isPrivate}`);
    }
    if (tags !== undefined && tags !== null && tags.length > 0) {
      queryParams.push(`tags=${tags.join(encodeURIComponent(","))}`);
    }
    if (fields !== undefined && fields !== null && fields.length > 0) {
      queryParams.push(`fields=${fields.join(encodeURIComponent(","))}`);
    }

    if (sort !== undefined && sort !== null) {
      queryParams.push(`sort=${sort}`);
    } else {
      queryParams.push(`sort=-count(liked_by)`); // default sort
    }

    if (liked !== undefined && liked !== null) {
      queryParams.push(`liked=${liked}`);
    }

    if (filterByUser !== undefined && filterByUser !== null) {
      queryParams.push(`filter_by_user=${filterByUser}`);
    }

    if (page !== undefined) {
      queryParams.push(`page=${page ?? 1}`);
    }
    if (limit !== undefined) {
      queryParams.push(`limit=${limit ?? 9999999}`);
    }
    if (is_component !== null && is_component !== undefined) {
      queryParams.push(`is_component=${is_component}`);
    }
    if (queryParams.length > 0) {
      url += `?${queryParams.join("&")}`;
    }

    const res = await api.get(url);

    if (res.status === 200) {
      return res.data;
    }
  } catch (error) {
    throw error;
  }
}

/**
 * 根据 ID 获取单个组件详情
 * @param component_id - 组件 ID
 * @returns 组件详细数据
 */
export async function getComponent(component_id: string) {
  try {
    const res = await api.get(
      `${getBaseUrl()}store/components/${component_id}`,
    );
    if (res.status === 200) {
      return res.data;
    }
  } catch (error) {
    throw error;
  }
}

/**
 * 检查用户是否已配置 API 密钥
 * @returns 布尔值表示是否已配置
 */
export async function checkHasApiKey() {
  try {
    const res = await api.get(`${getBaseUrl()}store/check/api_key`);
    if (res?.status === 200) {
      return res.data;
    }
  } catch (error) {
    throw error;
  }
}

/**
 * 检查组件商店是否可用
 * @returns 布尔值表示商店是否可用
 */
export async function checkHasStore() {
  try {
    const res = await api.get(`${getBaseUrl()}store/check/`);
    if (res?.status === 200) {
      return res.data;
    }
  } catch (error) {
    throw error;
  }
}

/**
 * Updates an existing flow in the Store.
 *
 * @param {FlowType} updatedFlow - The updated flow data.
 * @returns {Promise<any>} The updated flow data.
 * @throws Will throw an error if the update fails.
 */
export async function updateFlowStore(
  newFlow: {
    name?: string;
    data: ReactFlowJsonObject | null;
    description?: string;
    style?: FlowStyleType;
    is_component?: boolean;
    parent?: string;
    last_tested_version?: string;
  },
  tags: string[],
  publicFlow = false,
  id: string,
): Promise<FlowType> {
  try {
    const response = await api.patch(`${getBaseUrl()}store/components/${id}`, {
      name: newFlow.name,
      data: newFlow.data,
      description: newFlow.description,
      is_component: newFlow.is_component,
      parent: newFlow.parent,
      tags: tags,
      private: !publicFlow,
      last_tested_version: newFlow.last_tested_version,
    });

    if (response.status !== 201) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response?.data;
  } catch (error) {
    console.error(error);
    throw error;
  }
}

/**
 * 获取流程中顶点的执行顺序
 * @param flowId - 流程 ID
 * @param startNodeId - 可选的起始节点 ID
 * @param stopNodeId - 可选的停止节点 ID
 * @param nodes - 节点数组
 * @param Edges - 边数组
 * @returns 顶点执行顺序数据
 */
export async function getVerticesOrder(
  flowId: string,
  startNodeId?: string | null,
  stopNodeId?: string | null,
  nodes?: Node[],
  Edges?: Edge[],
): Promise<AxiosResponse<VerticesOrderTypeAPI>> {
  // nodeId is optional and is a query parameter
  // if nodeId is not provided, the API will return all vertices
  const config: AxiosRequestConfig<any> = {};
  if (stopNodeId) {
    config["params"] = { stop_component_id: stopNodeId };
  } else if (startNodeId) {
    config["params"] = { start_component_id: startNodeId };
  }
  const data = {
    data: {},
  };
  if (nodes && Edges) {
    data["data"]["nodes"] = nodes;
    data["data"]["edges"] = Edges;
  }
  return await api.post(
    `${getBaseUrl()}build/${flowId}/vertices`,
    data,
    config,
  );
}

/**
 * 构建单个顶点
 * @param flowId - 流程 ID
 * @param vertexId - 顶点 ID
 * @param input_value - 输入值
 * @param files - 可选的文件列表
 * @returns 顶点构建结果
 */
export async function postBuildVertex(
  flowId: string,
  vertexId: string,
  input_value: string,
  files?: string[],
): Promise<AxiosResponse<VertexBuildTypeAPI>> {
  // input_value is optional and is a query parameter
  const data = {};
  if (typeof input_value !== "undefined") {
    data["inputs"] = {
      input_value: input_value,
      client_request_time: Date.now(), // Add client timestamp in milliseconds
    };
  }
  if (data && files) {
    data["files"] = files;
  }
  return await api.post(
    `${getBaseUrl()}build/${flowId}/vertices/${vertexId}`,
    data,
  );
}
