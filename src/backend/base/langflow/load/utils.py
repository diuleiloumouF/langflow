import httpx
from lfx.load.utils import UploadError, replace_tweaks_with_env, upload, upload_file

from langflow.services.database.models.flow.model import FlowBase


def get_flow(url: str, flow_id: str):
    """Get the details of a flow from Langflow.

    Args:
        url (str): The host URL of Langflow.
        port (int): The port number of Langflow.
        flow_id (UUID): The ID of the flow to retrieve.

    Returns:
        dict: A dictionary containing the details of the flow.

    Raises:
        UploadError: If an error occurs during the retrieval process.
    """
    # 从 Langflow 服务器获取指定流程的详细信息
    try:
        # 构建流程 API 请求 URL
        flow_url = f"{url}/api/v1/flows/{flow_id}"
        # 发送 GET 请求获取流程数据
        response = httpx.get(flow_url)
        # 如果请求成功，解析并返回流程数据
        if response.status_code == httpx.codes.OK:
            json_response = response.json()
            return FlowBase(**json_response).model_dump()
    except Exception as e:
        # 获取流程失败时抛出上传错误
        msg = f"Error retrieving flow: {e}"
        raise UploadError(msg) from e


# 模块公开的 API 列表
__all__ = ["UploadError", "get_flow", "replace_tweaks_with_env", "upload", "upload_file"]
