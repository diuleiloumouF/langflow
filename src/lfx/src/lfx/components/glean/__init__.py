# 从 gleam_search_api 模块导入 Glean 搜索 API 的 Schema 定义
from .glean_search_api import GleanSearchAPISchema

# 模块公开接口，仅导出 GleanSearchAPISchema
__all__ = ["GleanSearchAPISchema"]
