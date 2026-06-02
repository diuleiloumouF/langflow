# 知识库相关常量定义
MAX_RETRY_ATTEMPTS = 5  # 最大重试次数
INGESTION_BATCH_SIZE = 200  # 数据摄入批处理大小
EXPONENTIAL_BACKOFF_MULTIPLIER = 2  # 指数退避乘数
MIN_KB_NAME_LENGTH = 3  # 知识库名称最小长度
CHUNK_PREVIEW_MULTIPLIER = 3  # 分块预览倍数

# 知识库删除重试常量
MAX_DELETE_RETRIES = 5  # 最大删除重试次数
DELETE_BACKOFF_SECONDS = 0.5  # 删除重试退避时间（秒）
