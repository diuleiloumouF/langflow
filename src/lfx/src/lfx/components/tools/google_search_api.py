# 导入 langchain 工具类
from langchain_core.tools import Tool

# 导入 LCToolComponent 基类，用于构建基于 langchain 的工具组件
from lfx.base.langchain_utilities.model import LCToolComponent

# 导入输入类型定义：IntInput 整数输入、MultilineInput 多行文本输入、SecretStrInput 密钥字符串输入
from lfx.inputs.inputs import IntInput, MultilineInput, SecretStrInput

# 导入 Data 数据模型，用于封装搜索结果
from lfx.schema.data import Data


# Google Search API 组件（已废弃）
# 该组件封装了 Google Custom Search API，提供网页搜索功能
# 标记为 legacy=True 表示此组件已废弃，保留仅为向后兼容旧流程
class GoogleSearchAPIComponent(LCToolComponent):
    # 组件在画布上显示的名称，[DEPRECATED] 标记表示已废弃
    display_name = "Google Search API [DEPRECATED]"
    # 组件描述，简要说明该组件的功能
    description = "Call Google Search API."
    # 组件内部标识名，用于在流程 JSON 中唯一标识该组件
    name = "GoogleSearchAPI"
    # 组件图标
    icon = "Google"
    # 标记为 legacy 组件，新建流程不应使用此组件
    legacy = True
    # 组件输入参数列表
    inputs = [
        # Google API 密钥，用于身份验证
        SecretStrInput(name="google_api_key", display_name="Google API Key", required=True),
        # Google 自定义搜索引擎 ID（CSE ID）
        SecretStrInput(name="google_cse_id", display_name="Google CSE ID", required=True),
        # 搜索查询输入框，支持多行文本
        MultilineInput(
            name="input_value",
            display_name="Input",
        ),
        # 返回的搜索结果数量，默认为 4 条
        IntInput(name="k", display_name="Number of results", value=4, required=True),
    ]

    # 执行模型运行，调用 Google Search API 并返回搜索结果
    # 返回值为 Data 对象列表，每个对象包含一条搜索结果
    def run_model(self) -> Data | list[Data]:
        # 构建 Google Search API 包装器
        wrapper = self._build_wrapper()
        # 执行搜索查询，获取指定数量的结果
        results = wrapper.results(query=self.input_value, num_results=self.k)
        # 将每条结果封装为 Data 对象，text 字段使用搜索结果的摘要片段
        data = [Data(data=result, text=result["snippet"]) for result in results]
        # 将结果保存到组件状态，供后续节点或 UI 展示使用
        self.status = data
        return data

    # 构建 langchain Tool 对象，将 Google Search 封装为可被 Agent 调用的工具
    def build_tool(self) -> Tool:
        wrapper = self._build_wrapper()
        return Tool(
            # 工具名称，Agent 通过此名称调用该工具
            name="google_search",
            # 工具描述，Agent 根据此描述决定是否使用该工具
            description="Search Google for recent results.",
            # 绑定到 Google Search API 包装器的 run 方法
            func=wrapper.run,
        )

    # 构建 Google Search API 包装器实例
    # 使用延迟导入避免在组件未使用时引入 langchain_google_community 依赖
    def _build_wrapper(self):
        try:
            # 从 langchain-google-community 包导入 GoogleSearchAPIWrapper
            from langchain_google_community import GoogleSearchAPIWrapper
        except ImportError as e:
            # 如果未安装依赖包，抛出带有安装提示的导入错误
            msg = "Please install langchain-google-community to use GoogleSearchAPIWrapper."
            raise ImportError(msg) from e
        # 使用 API 密钥、CSE ID 和结果数量创建包装器实例
        return GoogleSearchAPIWrapper(google_api_key=self.google_api_key, google_cse_id=self.google_cse_id, k=self.k)
