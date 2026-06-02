# HTTP 响应压缩工具模块
# 提供 gzip 压缩功能，用于减少 API 响应的数据传输量
import gzip
import json
from typing import Any

from fastapi import Response
from fastapi.encoders import jsonable_encoder


# 将数据压缩为 gzip 格式的 FastAPI Response 对象
def compress_response(data: Any) -> Response:
    """Compress data and return it as a FastAPI Response with appropriate headers."""
    json_data = json.dumps(jsonable_encoder(data)).encode("utf-8")

    compressed_data = gzip.compress(json_data, compresslevel=6)

    return Response(
        content=compressed_data,
        media_type="application/json",
        headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding", "Content-Length": str(len(compressed_data))},
    )
