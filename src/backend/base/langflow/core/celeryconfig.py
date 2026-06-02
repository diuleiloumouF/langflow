# celeryconfig.py - Celery 配置文件
import os

# 从环境变量获取 Redis 连接信息
langflow_redis_host = os.environ.get("LANGFLOW_REDIS_HOST")
langflow_redis_port = os.environ.get("LANGFLOW_REDIS_PORT")
# broker 默认用户

# 如果配置了 Redis 连接信息，使用 Redis 作为消息代理和结果后端
if langflow_redis_host and langflow_redis_port:
    broker_url = f"redis://{langflow_redis_host}:{langflow_redis_port}/0"
    result_backend = f"redis://{langflow_redis_host}:{langflow_redis_port}/0"
else:
    # 未配置 Redis 时，使用 RabbitMQ 作为消息代理
    mq_user = os.environ.get("RABBITMQ_DEFAULT_USER", "langflow")
    mq_password = os.environ.get("RABBITMQ_DEFAULT_PASS", "langflow")
    broker_url = os.environ.get("BROKER_URL", f"amqp://{mq_user}:{mq_password}@localhost:5672//")
    result_backend = os.environ.get("RESULT_BACKEND", "redis://localhost:6379/0")
# 任务序列化格式：支持 json 和 pickle
accept_content = ["json", "pickle"]
