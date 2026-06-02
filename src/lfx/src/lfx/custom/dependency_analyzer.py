"""自定义组件的依赖分析工具模块。"""

from __future__ import annotations

import ast
import importlib.metadata as md
import sys
from dataclasses import asdict, dataclass
from functools import lru_cache

# 标准库模块集合，用于过滤标准库导入
try:
    STDLIB_MODULES: set[str] = set(sys.stdlib_module_names)  # 3.10+
except AttributeError:
    # Fallback heuristic if running on <3.10
    # 低于 Python 3.10 版本时使用内置模块名作为回退方案
    STDLIB_MODULES = set(sys.builtin_module_names)


@dataclass(frozen=True)
class DependencyInfo:
    """Python 代码中导入的依赖信息。"""

    name: str  # 包名（例如 "numpy", "requests"）
    version: str | None  # 包版本（如果可用）
    is_local: bool  # True 表示相对导入（from .module import ...）


def _top_level(pkg: str) -> str:
    """提取顶层包名。"""
    return pkg.split(".", 1)[0]


def _is_relative(module: str | None) -> bool:
    """检查模块是否是相对导入。"""
    return module is not None and module.startswith(".")


class _ImportVisitor(ast.NodeVisitor):
    """AST 访问者，用于提取导入信息。"""

    def __init__(self):
        """初始化导入访问者。"""
        self.results: list[DependencyInfo] = []

    def visit_Import(self, node: ast.Import):
        """处理 import 语句。"""
        for alias in node.names:
            full = alias.name
            dep = DependencyInfo(
                name=_top_level(full),
                version=None,
                is_local=False,  # Regular imports are not local
            )
            self.results.append(dep)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """处理 from...import 语句。"""
        # Reconstruct full module name with proper relative import handling
        # 使用正确的相对导入处理重建完整模块名
        if node.level > 0:
            # Relative import: from .module import x or from ..parent import x
            # 相对导入：from .module import x 或 from ..parent import x
            dots = "." * node.level
            full_module = dots + (node.module or "")
        else:
            # Absolute import: from module import x
            # 绝对导入：from module import x
            full_module = node.module or ""
        for _alias in node.names:
            dep = DependencyInfo(
                name=_top_level(full_module.lstrip(".")) if full_module else "",
                version=None,
                is_local=_is_relative(full_module),  # Check if it's a relative import
            )
            self.results.append(dep)


def _classify_dependency(dep: DependencyInfo) -> DependencyInfo:
    """为外部依赖解析版本信息。"""
    version = None
    if not dep.is_local and dep.name:
        version = _get_distribution_version(dep.name)

    return DependencyInfo(
        name=dep.name,
        version=version,
        is_local=dep.is_local,
    )


def analyze_dependencies(source: str, *, resolve_versions: bool = True) -> list[dict]:
    """分析给定 Python 源代码中导入的依赖，返回依赖列表。

    Args:
        source: Python 源代码字符串
        resolve_versions: 是否解析版本信息

    Returns:
        依赖字典列表
    """
    code = source

    # Parse the code and extract imports
    # 解析代码并提取导入语句
    tree = ast.parse(code)
    visitor = _ImportVisitor()
    visitor.visit(tree)

    # Process and deduplicate dependencies by package name only
    # 按包名处理和去重依赖
    unique_packages: dict[str, DependencyInfo] = {}
    for raw_dep in visitor.results:
        processed_dep = _classify_dependency(raw_dep) if resolve_versions else raw_dep

        # Skip stdlib imports and local imports - we only care about external dependencies
        # 跳过标准库导入和本地导入 - 我们只关心外部依赖
        if processed_dep.name in STDLIB_MODULES or processed_dep.is_local:
            continue

        # Deduplicate by package name only (not full_module)
        # 仅按包名去重（不是完整模块名）
        if processed_dep.name not in unique_packages:
            unique_packages[processed_dep.name] = processed_dep

    return [asdict(d) for d in unique_packages.values()]


def analyze_component_dependencies(component_code: str) -> dict:
    """分析自定义组件的依赖。

    Args:
        component_code: 组件的源代码

    Returns:
        包含依赖分析结果的字典
    """
    try:
        deps = analyze_dependencies(component_code, resolve_versions=True)

        return {
            "total_dependencies": len(deps),
            "dependencies": [{"name": d["name"], "version": d["version"]} for d in deps if d["name"]],
        }
    except (SyntaxError, TypeError, ValueError, ImportError):
        # If analysis fails, return minimal info
        # 如果分析失败，返回最小信息
        return {
            "total_dependencies": 0,
            "dependencies": [],
        }


# 缓存昂贵的 packages_distributions() 全局调用
# Cache the expensive packages_distributions() call globally
@lru_cache(maxsize=1)
def _get_packages_distributions():
    """缓存昂贵的 packages_distributions() 调用。"""
    try:
        return md.packages_distributions()
    except (OSError, AttributeError, ValueError):
        return {}


# 缓存已安装发行版的版本查询辅助函数
# Helper function to cache version lookups for installed distributions
@lru_cache(maxsize=128)
def _get_distribution_version(import_name: str):
    """获取导入名称对应的发行版版本。"""
    try:
        # Reverse-lookup: which distribution(s) provide this importable name?
        # 反向查找：哪个发行版提供了这个可导入的名称？
        reverse_map = _get_packages_distributions()
        dist_names = reverse_map.get(import_name)
        if not dist_names:
            return None

        # Sort for deterministic selection when multiple distributions provide the same import
        # 排序以确定性选择当多个发行版提供相同导入时
        dist_name = sorted(dist_names)[0]
        return md.distribution(dist_name).version
    except (ImportError, AttributeError, OSError, ValueError):
        return None
