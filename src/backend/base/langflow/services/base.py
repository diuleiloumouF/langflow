from abc import ABC


# 服务基类，所有服务的抽象父类
class Service(ABC):
    # 服务名称
    name: str
    # 服务是否就绪的标志
    ready: bool = False

    # 构建服务的 JSON Schema，用于向外部暴露服务可用的方法和签名
    def get_schema(self):
        """Build a dictionary listing all methods, their parameters, types, return types and documentation."""
        # schema 字典：key 为方法名，value 为方法签名信息
        schema = {}
        # 需要排除的内部方法列表
        ignore = ["teardown", "set_ready"]
        for method in dir(self):
            # 跳过私有方法和需要排除的方法
            if method.startswith("_") or method in ignore:
                continue
            # 获取方法对象
            func = getattr(self, method)
            # 将方法的参数、返回值、文档字符串组装为 schema 条目
            schema[method] = {
                "name": method,
                "parameters": func.__annotations__,
                "return": func.__annotations__.get("return"),
                "documentation": func.__doc__,
            }
        return schema

    # 异步关闭服务，子类可重写以释放资源
    async def teardown(self) -> None:
        return

    # 标记服务为就绪状态
    def set_ready(self) -> None:
        self.ready = True
