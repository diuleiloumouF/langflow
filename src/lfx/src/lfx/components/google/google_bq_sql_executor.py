# JSON 序列化与反序列化工具
import json

# 正则表达式模块，用于 SQL 查询清理
import re

# 路径操作工具
from pathlib import Path

# Google 认证相关异常
from google.auth.exceptions import RefreshError

# Google BigQuery 客户端库
from google.cloud import bigquery

# Google OAuth2 服务账号凭证类
from google.oauth2.service_account import Credentials

# Langflow 组件基类
from lfx.custom import Component

# Langflow 组件输入输出类型
from lfx.io import BoolInput, FileInput, MessageTextInput, Output

# Langflow DataFrame 数据结构，用于返回查询结果
from lfx.schema.dataframe import DataFrame


class BigQueryExecutorComponent(Component):
    """BigQuery SQL 执行器组件。

    该组件允许用户通过上传 Google Cloud 服务账号 JSON 凭证文件，
    在 Google BigQuery 上执行 SQL 查询，并将结果以 DataFrame 形式返回。
    """

    display_name = "BigQuery"
    description = "Execute SQL queries on Google BigQuery."
    name = "BigQueryExecutor"
    icon = "Google"
    beta: bool = True

    # 组件输入参数定义
    inputs = [
        FileInput(
            name="service_account_json_file",
            display_name="Upload Service Account JSON",
            info="Upload the JSON file containing Google Cloud service account credentials.",
            file_types=["json"],
            required=True,
        ),
        MessageTextInput(
            name="query",
            display_name="SQL Query",
            info="The SQL query to execute on BigQuery.",
            required=True,
            tool_mode=True,
        ),
        BoolInput(
            name="clean_query",
            display_name="Clean Query",
            info="When enabled, this will automatically clean up your SQL query.",
            value=False,
            advanced=True,
        ),
    ]

    # 组件输出参数定义
    outputs = [
        Output(display_name="Query Results", name="query_results", method="execute_sql"),
    ]

    # SQL 查询清理私有方法
    def _clean_sql_query(self, query: str) -> str:
        """Clean SQL query by removing surrounding quotes and whitespace.

        Also extracts SQL statements from text that might contain other content.

        Args:
            query: The SQL query to clean

        Returns:
            The cleaned SQL query
        """
        # 清理 SQL 查询：移除多余的引号、空白字符，并从混合文本中提取纯 SQL 语句

        # 首先尝试从 Markdown 代码块中提取 SQL
        sql_pattern = r"```(?:sql)?\s*([\s\S]*?)\s*```"
        sql_matches = re.findall(sql_pattern, query, re.IGNORECASE)

        if sql_matches:
            # 如果在代码块中找到了 SQL，使用第一个匹配结果
            query = sql_matches[0]
        else:
            # 如果没有代码块，尝试通过常见 SQL 关键字定位 SQL 语句
            # 查找以 SQL 关键字开头的行
            sql_keywords = r"(?i)(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH|MERGE)"
            lines = query.split("\n")
            sql_lines = []
            in_sql = False

            for _line in lines:
                line = _line.strip()
                if re.match(sql_keywords, line):
                    in_sql = True
                if in_sql:
                    sql_lines.append(line)
                if line.endswith(";"):
                    in_sql = False

            if sql_lines:
                query = "\n".join(sql_lines)

        # 移除首尾的反引号
        query = query.strip("`")

        # 移除首尾的引号（单引号或双引号）
        query = query.strip()
        if (query.startswith('"') and query.endswith('"')) or (query.startswith("'") and query.endswith("'")):
            query = query[1:-1]

        # 清理多余的空白字符，确保没有残留的反引号
        query = query.strip()
        # 移除不属于有效标识符的反引号（保留表名/列名中的反引号）
        # 此正则表达式会移除不是标识符一部分的反引号
        return re.sub(r"`(?![a-zA-Z0-9_])|(?<![a-zA-Z0-9_])`", "", query)

    # 执行 SQL 查询主方法
    def execute_sql(self) -> DataFrame:
        """执行 BigQuery SQL 查询并返回结果。

        读取服务账号凭证文件，建立 BigQuery 客户端连接，
        执行用户输入的 SQL 查询，将结果转换为 DataFrame 返回。

        Returns:
            DataFrame: 包含查询结果的数据框

        Raises:
            ValueError: 当凭证文件不存在、JSON 格式错误、缺少 project_id
                       或查询为空时抛出异常
        """
        try:
            # 尝试读取服务账号 JSON 凭证文件
            try:
                service_account_path = Path(self.service_account_json_file)
                with service_account_path.open() as f:
                    credentials_json = json.load(f)
                    project_id = credentials_json.get("project_id")
                    if not project_id:
                        msg = "No project_id found in service account credentials file."
                        raise ValueError(msg)
            except FileNotFoundError as e:
                msg = f"Service account file not found: {e}"
                raise ValueError(msg) from e
            except json.JSONDecodeError as e:
                msg = "Invalid JSON string for service account credentials"
                raise ValueError(msg) from e

            # 尝试从文件加载 Google OAuth2 服务账号凭证
            try:
                credentials = Credentials.from_service_account_file(self.service_account_json_file)
            except Exception as e:
                msg = f"Error loading service account credentials: {e}"
                raise ValueError(msg) from e

        except ValueError:
            raise
        except Exception as e:
            msg = f"Error executing BigQuery SQL query: {e}"
            raise ValueError(msg) from e

        try:
            # 创建 BigQuery 客户端实例
            client = bigquery.Client(credentials=credentials, project=project_id)

            # 在清理之前检查查询是否为空或仅包含空白字符
            if not str(self.query).strip():
                msg = "No valid SQL query found in input text."
                raise ValueError(msg)

            # 如果查询包含代码块标记、引号，或者启用了清理选项，则执行查询清理
            if "```" in str(self.query) or '"' in str(self.query) or "'" in str(self.query) or self.clean_query:
                sql_query = self._clean_sql_query(str(self.query))
            else:
                sql_query = str(self.query).strip()  # 至少去除首尾空白字符

            # 执行 SQL 查询并获取结果
            query_job = client.query(sql_query)
            results = query_job.result()
            # 将查询结果的每一行转换为字典列表
            output_dict = [dict(row) for row in results]

        except RefreshError as e:
            # 认证令牌刷新失败，提示用户重新认证
            msg = "Authentication error: Unable to refresh authentication token. Please try to reauthenticate."
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"Error executing BigQuery SQL query: {e}"
            raise ValueError(msg) from e

        # 将查询结果封装为 DataFrame 返回
        return DataFrame(output_dict)
