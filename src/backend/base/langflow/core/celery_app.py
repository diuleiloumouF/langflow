from celery import Celery


def make_celery(app_name: str, config: str) -> Celery:
    """创建并配置 Celery 应用实例。"""
    # 创建 Celery 应用
    celery_app = Celery(app_name)
    # 从指定配置模块加载配置
    celery_app.config_from_object(config)
    # 设置任务路由规则：将 langflow.worker.tasks 下的任务路由到 langflow 队列
    celery_app.conf.task_routes = {"langflow.worker.tasks.*": {"queue": "langflow"}}
    return celery_app


# 创建全局 Celery 应用实例
celery_app = make_celery("langflow", "langflow.core.celeryconfig")
