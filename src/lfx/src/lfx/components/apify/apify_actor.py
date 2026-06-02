import json
import string
from typing import Any, cast

from apify_client import ApifyClient
from langchain_community.document_loaders.apify_dataset import ApifyDatasetLoader
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, field_serializer

from lfx.custom.custom_component.component import Component
from lfx.field_typing import Tool
from lfx.inputs.inputs import BoolInput
from lfx.io import MultilineInput, Output, SecretStrInput, StrInput
from lfx.schema.data import Data

# 数据集字段描述的最大长度限制
MAX_DESCRIPTION_LEN = 250


# Apify Actors 组件，用于调用 Apify 平台的 Actor 来抓取数据，支持作为 Agent 工具使用
class ApifyActorsComponent(Component):
    display_name = "Apify Actors"
    description = (
        "Use Apify Actors to extract data from hundreds of places fast. "
        "This component can be used in a flow to retrieve data or as a tool with an agent."
    )
    documentation: str = "https://docs.langflow.org/bundles-apify"
    icon = "Apify"
    name = "ApifyActors"

    inputs = [
        SecretStrInput(
            name="apify_token",
            display_name="Apify Token",
            info="The API token for the Apify account.",
            required=True,
            password=True,
        ),
        StrInput(
            name="actor_id",
            display_name="Actor",
            info=(
                "Actor name from Apify store to run. For example 'apify/website-content-crawler' "
                "to use the Website Content Crawler Actor."
            ),
            value="apify/website-content-crawler",
            required=True,
        ),
        # multiline input is more pleasant to use than the nested dict input
        # 多行输入比嵌套字典输入更易用
        MultilineInput(
            name="run_input",
            display_name="Run input",
            info=(
                'The JSON input for the Actor run. For example for the "apify/website-content-crawler" Actor: '
                '{"startUrls":[{"url":"https://docs.apify.com/academy/web-scraping-for-beginners"}],"maxCrawlDepth":0}'
            ),
            value='{"startUrls":[{"url":"https://docs.apify.com/academy/web-scraping-for-beginners"}],"maxCrawlDepth":0}',
            required=True,
        ),
        MultilineInput(
            name="dataset_fields",
            display_name="Output fields",
            info=(
                "Fields to extract from the dataset, split by commas. "
                "Other fields will be ignored. Dots in nested structures will be replaced by underscores. "
                "Sample input: 'text, metadata.title'. "
                "Sample output: {'text': 'page content here', 'metadata_title': 'page title here'}. "
                "For example, for the 'apify/website-content-crawler' Actor, you can extract the 'markdown' field, "
                "which is the content of the website in markdown format."
            ),
        ),
        BoolInput(
            name="flatten_dataset",
            display_name="Flatten output",
            info=(
                "The output dataset will be converted from a nested format to a flat structure. "
                "Dots in nested structure will be replaced by underscores. "
                "This is useful for further processing of the Data object. "
                "For example, {'a': {'b': 1}} will be flattened to {'a_b': 1}."
            ),
        ),
    ]

    # 组件输出：数据输出和 Agent 工具
    outputs = [
        Output(display_name="Output", name="output", type_=list[Data], method="run_model"),
        Output(display_name="Tool", name="tool", type_=Tool, method="build_tool"),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._apify_client: ApifyClient | None = None

    def run_model(self) -> list[Data]:
        """Run the Actor and return node output."""
        # 解析用户输入的 JSON 字符串
        input_ = json.loads(self.run_input)
        # 解析需要提取的数据集字段
        fields = ApifyActorsComponent.parse_dataset_fields(self.dataset_fields) if self.dataset_fields else None
        # 执行 Actor 并获取结果
        res = self.run_actor(self.actor_id, input_, fields=fields)
        # 如果开启了扁平化输出，则将嵌套结构展开
        if self.flatten_dataset:
            res = [ApifyActorsComponent.flatten(item) for item in res]
        # 将字典列表转换为 Data 对象列表
        data = [Data(data=item) for item in res]

        self.status = data
        return data

    def build_tool(self) -> Tool:
        """Build a tool for an agent that runs the Apify Actor."""
        actor_id = self.actor_id

        # 获取 Actor 最新构建信息
        build = self._get_actor_latest_build(actor_id)
        readme = build.get("readme", "")[:250] + "..."
        if not (input_schema_str := build.get("inputSchema")):
            msg = "Input schema not found"
            raise ValueError(msg)
        input_schema = json.loads(input_schema_str)
        # 从构建信息中提取输入模式（参数定义和必填字段）
        properties, required = ApifyActorsComponent.get_actor_input_schema_from_build(input_schema)
        properties = {"run_input": properties}

        # works from input schema
        # 根据输入模式生成工具描述信息
        info_ = [
            (
                "JSON encoded as a string with input schema (STRICTLY FOLLOW JSON FORMAT AND SCHEMA):\n\n"
                f"{json.dumps(properties, separators=(',', ':'))}"
            )
        ]
        if required:
            info_.append("\n\nRequired fields:\n" + "\n".join(required))

        info = "".join(info_)

        # 动态创建 Pydantic 输入模型类
        input_model_cls = ApifyActorsComponent.create_input_model_class(info)
        # 动态创建工具类
        tool_cls = ApifyActorsComponent.create_tool_class(self, readme, input_model_cls, actor_id)

        return cast("Tool", tool_cls())

    @staticmethod
    def create_tool_class(
        parent: "ApifyActorsComponent", readme: str, input_model: type[BaseModel], actor_id: str
    ) -> type[BaseTool]:
        """Create a tool class that runs an Apify Actor."""

        # 动态创建的 Apify Actor 运行工具类
        class ApifyActorRun(BaseTool):
            """Tool that runs Apify Actors."""

            name: str = f"apify_actor_{ApifyActorsComponent.actor_id_to_tool_name(actor_id)}"
            description: str = (
                "Run an Apify Actor with the given input. "
                "Here is a part of the currently loaded Actor README:\n\n"
                f"{readme}\n\n"
            )

            args_schema: type[BaseModel] = input_model

            @field_serializer("args_schema")
            def serialize_args_schema(self, args_schema):
                return args_schema.schema()

            def _run(self, run_input: str | dict) -> str:
                """Use the Apify Actor."""
                # 将字符串输入解析为字典
                input_dict = json.loads(run_input) if isinstance(run_input, str) else run_input

                # retrieve if nested, just in case
                # 如果输入被嵌套在 run_input 键中，提取出来
                input_dict = input_dict.get("run_input", input_dict)

                # 调用父组件的 run_actor 方法执行 Actor
                res = parent.run_actor(actor_id, input_dict)
                return "\n\n".join([ApifyActorsComponent.dict_to_json_str(item) for item in res])

        return ApifyActorRun

    @staticmethod
    def create_input_model_class(description: str) -> type[BaseModel]:
        """Create a Pydantic model class for the Actor input."""

        # 动态创建的 Actor 输入模型类
        class ActorInput(BaseModel):
            """Input for the Apify Actor tool."""

            run_input: str = Field(..., description=description)

        return ActorInput

    def _get_apify_client(self) -> ApifyClient:
        """Get the Apify client.

        Is created if not exists or token changes.
        """
        if not self.apify_token:
            msg = "API token is required."
            raise ValueError(msg)
        # when token changes, create a new client
        # 当 token 发生变化时，创建新的客户端
        if self._apify_client is None or self._apify_client.token != self.apify_token:
            self._apify_client = ApifyClient(self.apify_token)
            if httpx_client := self._apify_client.http_client.httpx_client:
                httpx_client.headers["user-agent"] += "; Origin/langflow"
        return self._apify_client

    def _get_actor_latest_build(self, actor_id: str) -> dict:
        """Get the latest build of an Actor from the default build tag."""
        client = self._get_apify_client()
        actor = client.actor(actor_id=actor_id)
        # 获取 Actor 信息，如果不存在则抛出异常
        if not (actor_info := actor.get()):
            msg = f"Actor {actor_id} not found."
            raise ValueError(msg)

        # 获取默认构建标签对应的最新构建 ID
        default_build_tag = actor_info.get("defaultRunOptions", {}).get("build")
        latest_build_id = actor_info.get("taggedBuilds", {}).get(default_build_tag, {}).get("buildId")

        if (build := client.build(latest_build_id).get()) is None:
            msg = f"Build {latest_build_id} not found."
            raise ValueError(msg)

        return build

    @staticmethod
    def get_actor_input_schema_from_build(input_schema: dict) -> tuple[dict, list[str]]:
        """Get the input schema from the Actor build.

        Trim the description to 250 characters.
        """
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        properties_out: dict = {}
        for item, meta in properties.items():
            properties_out[item] = {}
            # 截断过长的描述到最大长度
            if desc := meta.get("description"):
                properties_out[item]["description"] = (
                    desc[:MAX_DESCRIPTION_LEN] + "..." if len(desc) > MAX_DESCRIPTION_LEN else desc
                )
            # 提取关键属性：type、default、prefill、enum
            for key_name in ("type", "default", "prefill", "enum"):
                if value := meta.get(key_name):
                    properties_out[item][key_name] = value

        return properties_out, required

    def _get_run_dataset_id(self, run_id: str) -> str:
        """Get the dataset id from the run id."""
        client = self._get_apify_client()
        run = client.run(run_id=run_id)
        if (dataset := run.dataset().get()) is None:
            msg = "Dataset not found"
            raise ValueError(msg)
        if (did := dataset.get("id")) is None:
            msg = "Dataset id not found"
            raise ValueError(msg)
        return did

    @staticmethod
    def dict_to_json_str(d: dict) -> str:
        """Convert a dictionary to a JSON string."""
        return json.dumps(d, separators=(",", ":"), default=lambda _: "<n/a>")

    @staticmethod
    def actor_id_to_tool_name(actor_id: str) -> str:
        """Turn actor_id into a valid tool name.

        Tool name must only contain letters, numbers, underscores, dashes,
            and cannot contain spaces.
        """
        # 只保留字母、数字、下划线和连字符，其他字符替换为下划线
        valid_chars = string.ascii_letters + string.digits + "_-"
        return "".join(char if char in valid_chars else "_" for char in actor_id)

    def run_actor(self, actor_id: str, run_input: dict, fields: list[str] | None = None) -> list[dict]:
        """Run an Apify Actor and return the output dataset.

        Args:
            actor_id: Actor name from Apify store to run.
            run_input: JSON input for the Actor.
            fields: List of fields to extract from the dataset. Other fields will be ignored.
        """
        client = self._get_apify_client()
        # 调用 Actor 并等待最多 1 秒，获取运行详情
        if (details := client.actor(actor_id=actor_id).call(run_input=run_input, wait_secs=1)) is None:
            msg = "Actor run details not found"
            raise ValueError(msg)
        if (run_id := details.get("id")) is None:
            msg = "Run id not found"
            raise ValueError(msg)

        if (run_client := client.run(run_id)) is None:
            msg = "Run client not found"
            raise ValueError(msg)

        # stream logs
        # 流式读取 Actor 运行日志并记录
        with run_client.log().stream() as response:
            if response:
                for line in response.iter_lines():
                    self.log(line)
        # 等待 Actor 运行完成
        run_client.wait_for_finish()

        # 获取运行结果对应的数据集 ID
        dataset_id = self._get_run_dataset_id(run_id)

        # 使用 ApifyDatasetLoader 加载数据集结果
        # 如果指定了 fields，只提取指定字段并替换点号为下划线
        loader = ApifyDatasetLoader(
            dataset_id=dataset_id,
            dataset_mapping_function=lambda item: item
            if not fields
            else {k.replace(".", "_"): ApifyActorsComponent.get_nested_value(item, k) for k in fields},
        )
        return loader.load()

    @staticmethod
    def get_nested_value(data: dict[str, Any], key: str) -> Any:
        """Get a nested value from a dictionary."""
        # 使用点号分隔的路径获取嵌套字典中的值
        keys = key.split(".")
        value = data
        for k in keys:
            if not isinstance(value, dict) or k not in value:
                return None
            value = value[k]
        return value

    @staticmethod
    def parse_dataset_fields(dataset_fields: str) -> list[str]:
        """Convert a string of comma-separated fields into a list of fields."""
        # 清除引号并按逗号分割字段
        dataset_fields = dataset_fields.replace("'", "").replace('"', "").replace("`", "")
        return [field.strip() for field in dataset_fields.split(",")]

    @staticmethod
    def flatten(d: dict) -> dict:
        """Flatten a nested dictionary."""

        def items():
            for key, value in d.items():
                if isinstance(value, dict):
                    # 递归展开嵌套字典，使用下划线连接键名
                    for subkey, subvalue in ApifyActorsComponent.flatten(value).items():
                        yield key + "_" + subkey, subvalue
                else:
                    yield key, value

        return dict(items())
