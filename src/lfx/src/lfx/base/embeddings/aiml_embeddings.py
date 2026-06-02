import concurrent.futures
import json

import httpx
from pydantic import BaseModel, SecretStr

from lfx.field_typing import Embeddings
from lfx.log.logger import logger


# AIML API 嵌入向量实现类，用于调用 AIML API 生成文本嵌入向量
class AIMLEmbeddingsImpl(BaseModel, Embeddings):
    # AIML API 嵌入接口的默认地址
    embeddings_completion_url: str = "https://api.aimlapi.com/v1/embeddings"

    # API 密钥，使用 SecretStr 进行安全存储
    api_key: SecretStr
    # 使用的嵌入模型名称
    model: str

    # 批量嵌入文档，支持并发请求以提高性能
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # 初始化结果列表，保持原始顺序
        embeddings = [None] * len(texts)
        # 设置请求头，包含内容类型和授权信息
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key.get_secret_value()}",
        }

        # 使用线程池并发执行嵌入请求，提高批量处理效率
        with httpx.Client() as client, concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for i, text in enumerate(texts):
                # 提交异步嵌入任务，返回索引和 Future 对象
                futures.append((i, executor.submit(self._embed_text, client, headers, text)))

            # 收集所有任务结果并按原始顺序填入结果列表
            for index, future in futures:
                try:
                    result_data = future.result()
                    # 验证返回的嵌入向量数量是否符合预期
                    if len(result_data["data"]) != 1:
                        msg = f"Expected one embedding, got {len(result_data['data'])}"
                        raise ValueError(msg)
                    # 提取嵌入向量并按原始索引存储
                    embeddings[index] = result_data["data"][0]["embedding"]
                except (
                    httpx.HTTPStatusError,
                    httpx.RequestError,
                    json.JSONDecodeError,
                    KeyError,
                    ValueError,
                ):
                    # 记录异常详情并重新抛出错误
                    logger.exception("Error occurred")
                    raise

        return embeddings  # type: ignore[return-value]

    # 向 AIML API 发送单条文本嵌入请求
    def _embed_text(self, client: httpx.Client, headers: dict, text: str) -> dict:
        # 构建请求体，包含模型名称和待嵌入的文本
        payload = {
            "model": self.model,
            "input": text,
        }
        # 发送 POST 请求到嵌入接口
        response = client.post(
            self.embeddings_completion_url,
            headers=headers,
            json=payload,
        )
        # 检查响应状态码，非 2xx 状态码会抛出异常
        response.raise_for_status()
        # 解析并返回 JSON 格式的响应数据
        return response.json()

    # 嵌入单条查询文本，内部调用 embed_documents 方法处理
    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
