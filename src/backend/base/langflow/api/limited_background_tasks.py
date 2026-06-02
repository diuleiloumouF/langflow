# 导入 FastAPI 的 BackgroundTasks 基类
from fastapi import BackgroundTasks

# 导入顶点构建日志函数
from lfx.graph.utils import log_vertex_build

# 导入设置服务依赖注入函数
from langflow.services.deps import get_settings_service


# 限制顶点构建后台任务数量的子类
class LimitVertexBuildBackgroundTasks(BackgroundTasks):
    """A subclass of FastAPI BackgroundTasks that limits the number of tasks added per vertex_id.

    如果为某个 vertex_id 添加的任务数量超过 max_vertex_builds_per_vertex，则移除最旧的任务，
    只保留最近的任务。此限制仅适用于 log_vertex_build 任务。
    """

    # 重写添加任务方法，添加限制逻辑
    def add_task(self, func, *args, **kwargs):
        # 仅对 log_vertex_build 任务应用限制逻辑
        # Only apply limiting logic to log_vertex_build tasks
        if func == log_vertex_build:
            # 获取当前任务对应的顶点 ID
            vertex_id = kwargs.get("vertex_id")
            if vertex_id is not None:
                # 筛选出与当前顶点 ID 相同的 log_vertex_build 调用任务
                # Filter tasks that are log_vertex_build calls with the same vertex_id
                relevant_tasks = [
                    t for t in self.tasks if t.func == log_vertex_build and t.kwargs.get("vertex_id") == vertex_id
                ]
                # 如果相关任务数量达到上限，移除最旧的任务
                if len(relevant_tasks) >= get_settings_service().settings.max_vertex_builds_per_vertex:
                    # Remove the oldest task for this vertex_id
                    oldest_task = relevant_tasks[0]
                    self.tasks.remove(oldest_task)

        # 调用父类的 add_task 方法添加新任务
        super().add_task(func, *args, **kwargs)
