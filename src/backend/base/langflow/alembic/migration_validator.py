"""Migration Validator - Enforces Expand-Contract Pattern for Alembic migrations."""

# 迁移验证器 - 对 Alembic 迁移强制执行"扩展-收缩"模式
# 该工具通过 AST 分析确保迁移脚本遵循安全的数据库变更模式

import ast
import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


# 迁移阶段枚举，对应"扩展-收缩"模式的三个阶段
class MigrationPhase(Enum):
    EXPAND = "EXPAND"  # 扩展阶段：添加新列、新表等，不影响现有数据
    MIGRATE = "MIGRATE"  # 迁移阶段：数据迁移和转换
    CONTRACT = "CONTRACT"  # 收缩阶段：删除旧列、旧表等废弃结构
    UNKNOWN = "UNKNOWN"  # 未知阶段：未标记阶段的迁移


# 违规记录数据类，用于存储验证过程中发现的问题
@dataclass
class Violation:
    type: str  # 违规类型代码
    message: str  # 违规描述信息
    line: int  # 违规所在的行号
    severity: str = "error"  # 严重程度：error 或 warning


# 违规类型代码与描述的映射字典
VIOLATION_DESCRIPTIONS = {
    "BREAKING_ADD_COLUMN": "Adding non-nullable column without default",  # 添加非空列但没有默认值
    "DIRECT_RENAME": "Direct column rename detected",  # 直接重命名列（应使用扩展-收缩模式）
    "DIRECT_TYPE_CHANGE": "Direct type alteration detected",  # 直接修改列类型（应使用扩展-收缩模式）
    "IMMEDIATE_DROP": "Dropping column without migration phase",  # 未标记迁移阶段就删除列
    "MISSING_IDEMPOTENCY": "Migration not idempotent",  # 迁移脚本不具备幂等性
    "NO_PHASE_MARKER": "Migration missing phase documentation",  # 迁移脚本缺少阶段文档标记
    "UNSAFE_ROLLBACK": "Downgrade may cause data loss",  # 回滚操作可能导致数据丢失
    "MISSING_DOWNGRADE": "Downgrade function not implemented",  # 未实现 downgrade 函数
    "INVALID_PHASE_OPERATION": "Operation not allowed in this phase",  # 在当前阶段不允许的操作
    "NO_EXISTENCE_CHECK": "Operation should check existence first",  # 操作前应先检查是否存在
    "MISSING_DATA_CHECK": "CONTRACT phase should verify data migration",  # 收缩阶段应验证数据迁移
}


class MigrationValidator:
    """Validates Alembic migrations follow Expand-Contract pattern."""

    # 违规类型代码与描述的映射
    VIOLATIONS = VIOLATION_DESCRIPTIONS

    def __init__(self, *, strict_mode: bool = True):
        # 初始化验证器，strict_mode 为 True 时将警告视为错误
        self.strict_mode = strict_mode

    ### 主验证方法 - 模板方法模式（GoF 设计模式）###

    def validate_migration_file(self, filepath: Path) -> dict[str, Any]:
        """Validate a single migration file."""
        # 验证单个迁移文件是否符合扩展-收缩模式
        if not filepath.exists():
            return {
                "file": str(filepath),
                "valid": False,
                "violations": [Violation("FILE_NOT_FOUND", f"File not found: {filepath}", 0)],
                "warnings": [],
            }

        content = filepath.read_text()

        # 解析迁移文件的 Python 源代码为 AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {
                "file": str(filepath),
                "valid": False,
                "violations": [Violation("SYNTAX_ERROR", str(e), e.lineno or 0)],
                "warnings": [],
            }

        violations = []
        warnings = []

        # 检查迁移阶段文档标记
        phase = self._extract_phase(content)
        if phase == MigrationPhase.UNKNOWN:
            violations.append(
                Violation("NO_PHASE_MARKER", "Migration must specify phase: EXPAND, MIGRATE, or CONTRACT", 1)
            )

        # 检查 upgrade 函数
        upgrade_node = self._find_function(tree, "upgrade")
        if upgrade_node:
            phase_violations = self._check_upgrade_operations(upgrade_node, phase)
            violations.extend(phase_violations)
        else:
            violations.append(Violation("MISSING_UPGRADE", "Migration must have an upgrade() function", 1))

        # 检查 downgrade 函数
        downgrade_node = self._find_function(tree, "downgrade")
        if downgrade_node:
            downgrade_issues = self._check_downgrade_safety(downgrade_node, phase)
            warnings.extend(downgrade_issues)
        elif phase != MigrationPhase.CONTRACT:  # 收缩阶段可以不支持回滚
            violations.append(Violation("MISSING_DOWNGRADE", "Migration must have a downgrade() function", 1))

        # 针对收缩阶段的额外检查
        if phase == MigrationPhase.CONTRACT:
            contract_issues = self._check_contract_phase_requirements(content)
            violations.extend(contract_issues)

        return {
            "file": str(filepath),
            "valid": len(violations) == 0,
            "violations": [v.__dict__ for v in violations],
            "warnings": [w.__dict__ for w in warnings],
            "phase": phase.value,
        }

    # 检查数据库操作约束的方法
    # 新的约束需求应在此处添加

    def _check_upgrade_operations(self, node: ast.FunctionDef, phase: MigrationPhase) -> list[Violation]:
        """Check upgrade operations for violations."""
        # 检查 upgrade 函数中的操作是否违反扩展-收缩模式
        violations = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if self._is_op_call(child, "add_column"):
                    violations.extend(self._check_add_column(child, phase, node))

                elif self._is_op_call(child, "alter_column"):
                    violations.extend(self._check_alter_column(child, phase))

                elif self._is_op_call(child, "drop_column"):
                    violations.extend(self._check_drop_column(child, phase))

                elif self._is_op_call(child, "rename_table") or self._is_op_call(child, "rename_column"):
                    violations.append(
                        Violation("DIRECT_RENAME", "Use expand-contract pattern instead of direct rename", child.lineno)
                    )

        return violations

    def _check_add_column(self, call: ast.Call, phase: MigrationPhase, func_node: ast.FunctionDef) -> list[Violation]:
        """Check add_column operations."""
        # 检查 add_column 操作的合规性
        violations = []

        # 检查列是否可空或有默认值
        if not self._has_nullable_true(call) and not self._has_server_default(call):
            violations.append(
                Violation(
                    "BREAKING_ADD_COLUMN", "New columns must be nullable=True or have server_default", call.lineno
                )
            )

        # 检查幂等性：是否在添加列之前检查了列是否存在
        if not self._has_existence_check_nearby(func_node, call):
            violations.append(
                Violation(
                    "NO_EXISTENCE_CHECK", "add_column should check if column exists first (idempotency)", call.lineno
                )
            )

        # 收缩阶段不允许添加新列
        if phase == MigrationPhase.CONTRACT:
            violations.append(Violation("INVALID_PHASE_OPERATION", "Cannot add columns in CONTRACT phase", call.lineno))

        return violations

    def _check_alter_column(self, call: ast.Call, phase: MigrationPhase) -> list[Violation]:
        """Check alter_column operations."""
        # 检查 alter_column 操作的合规性
        violations = []

        # 检查类型变更：非收缩阶段不允许直接修改列类型
        if self._has_type_change(call) and phase != MigrationPhase.CONTRACT:
            violations.append(
                Violation("DIRECT_TYPE_CHANGE", "Type changes should use expand-contract pattern", call.lineno)
            )

        # 检查可空性变更：非收缩阶段不允许将列设为非空
        if self._changes_nullable_to_false(call) and phase != MigrationPhase.CONTRACT:
            violations.append(
                Violation(
                    "BREAKING_ADD_COLUMN", "Making column non-nullable only allowed in CONTRACT phase", call.lineno
                )
            )

        return violations

    def _check_drop_column(self, call: ast.Call, phase: MigrationPhase) -> list[Violation]:
        """Check drop_column operations."""
        # 检查 drop_column 操作的合规性
        violations = []

        # 只有收缩阶段才允许删除列
        if phase != MigrationPhase.CONTRACT:
            violations.append(
                Violation(
                    "IMMEDIATE_DROP",
                    f"Column drops only allowed in CONTRACT phase (current: {phase.value})",
                    call.lineno,
                )
            )

        return violations

    def _check_contract_phase_requirements(self, content: str) -> list[Violation]:
        """Check CONTRACT phase specific requirements."""
        # 检查收缩阶段的特定要求：删除列前应验证数据迁移
        if not ("SELECT" in content and "COUNT" in content):
            return [
                Violation(
                    "MISSING_DATA_CHECK",
                    "CONTRACT phase should verify data migration before dropping columns",
                    1,
                    severity="warning",
                )
            ]
        return []

    def _check_downgrade_safety(self, node: ast.FunctionDef, phase: MigrationPhase) -> list[Violation]:
        """Check downgrade function for safety issues."""
        # 检查 downgrade 函数的安全性问题
        warnings = []

        # 检查回滚操作是否可能导致数据丢失
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and self._is_op_call(child, "alter_column"):
                # 检查是否有备份机制
                func_content = ast.unparse(node)
                if "backup" not in func_content.lower() and "SELECT" not in func_content:
                    warnings.append(
                        Violation(
                            "UNSAFE_ROLLBACK",
                            "Downgrade drops column without checking/backing up data",
                            child.lineno,
                            severity="warning",
                        )
                    )

        # 收缩阶段的特殊处理：回滚应该抛出 NotImplementedError 或谨慎处理
        if phase == MigrationPhase.CONTRACT:
            func_content = ast.unparse(node)
            if "NotImplementedError" not in func_content and "raise" not in func_content:
                warnings.append(
                    Violation(
                        "UNSAFE_ROLLBACK",
                        "CONTRACT phase downgrade should raise NotImplementedError or handle carefully",
                        node.lineno,
                        severity="warning",
                    )
                )

        return warnings

    def _is_op_call(self, call: ast.Call, method: str) -> bool:
        """Check if call is op.method()."""
        # 检查函数调用是否为 op.method() 形式
        func = call.func

        # 避免多次属性解析和 isinstance 检查
        if type(func) is ast.Attribute:
            val = func.value
            if type(val) is ast.Name:
                return val.id == "op" and func.attr == method
        return False

    def _has_nullable_true(self, call: ast.Call) -> bool:
        """Check if call has nullable=True."""
        # 检查函数调用是否包含 nullable=True 参数
        for keyword in call.keywords:
            if keyword.arg == "nullable" and isinstance(keyword.value, ast.Constant):
                return keyword.value.value is True

        for call_arg in call.args:
            if isinstance(call_arg, ast.Call):
                return self._has_nullable_true(call_arg)

        return False

    def _has_server_default(self, call: ast.Call) -> bool:
        """Check if call has server_default."""
        # 检查函数调用是否包含 server_default 参数
        return any(kw.arg == "server_default" for kw in call.keywords)

    def _has_type_change(self, call: ast.Call) -> bool:
        """Check if alter_column changes type."""
        # 检查 alter_column 是否修改了列类型
        return any(kw.arg in ["type_", "type"] for kw in call.keywords)

    def _changes_nullable_to_false(self, call: ast.Call) -> bool:
        """Check if alter_column sets nullable=False."""
        # 检查 alter_column 是否将 nullable 设为 False
        for keyword in call.keywords:
            if keyword.arg == "nullable" and isinstance(keyword.value, ast.Constant):
                return keyword.value.value is False
        return False

    # 辅助方法：检查操作周围是否存在存在性检查
    # 查找可能检查列是否存在的 if 语句
    # TODO: 评估是否需要更复杂的分析来检测存在性检查
    def _has_existence_check_nearby(self, func_node: ast.FunctionDef, target_call: ast.Call) -> bool:
        """Check if operation is wrapped in existence check."""
        # 查找可能检查列是否存在的 if 语句
        for node in ast.walk(func_node):
            if isinstance(node, ast.If):
                # 检查此 if 语句是否包含目标调用
                for child in ast.walk(node):
                    if child == target_call:
                        # 检查条件是否提及列或检查器
                        condition = ast.unparse(node.test)
                        if any(keyword in condition.lower() for keyword in ["column", "inspector", "not in", "if not"]):
                            return True
        return False

    ### 辅助方法 ###

    def _extract_phase(self, content: str) -> MigrationPhase:
        """Extract migration phase from documentation."""
        # 从文档中提取迁移阶段标记
        # TODO: 支持从行内注释和函数注解中检测阶段，而不仅仅是文档字符串或顶层注释
        phase_pattern = r"Phase:\s*(EXPAND|MIGRATE|CONTRACT)"
        match = re.search(phase_pattern, content, re.IGNORECASE)

        if match:
            phase_str = match.group(1).upper()
            return MigrationPhase[phase_str]

        return MigrationPhase.UNKNOWN

    def _find_function(self, tree: ast.Module, name: str) -> ast.FunctionDef | None:
        """Find a function by name in the AST."""
        # 在 AST 中按名称查找函数定义
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return node
        return None


def main():
    """CLI entry point."""
    # 命令行入口点，用于验证迁移文件
    import argparse

    parser = argparse.ArgumentParser(description="Validate Alembic migrations")
    parser.add_argument("files", nargs="+", help="Migration files to validate")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")

    args = parser.parse_args()

    validator = MigrationValidator(strict_mode=args.strict)
    all_valid = True
    results = []

    # 逐个验证迁移文件
    for file_path in args.files:
        result = validator.validate_migration_file(Path(file_path))
        results.append(result)

        if not result["valid"]:
            all_valid = False

        # 严格模式下将警告也视为错误
        if args.strict and result["warnings"]:
            all_valid = False

    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("migration_validator")

    # 根据输出格式打印结果
    if args.json:
        import sys as _sys

        _sys.stdout.write(json.dumps(results, indent=2) + "\n")
    else:
        for result in results:
            logger.info("\n%s", "=" * 60)
            logger.info("File: %s", result["file"])
            logger.info("Phase: %s", result["phase"])
            logger.info("Valid: %s", "✅" if result["valid"] else "❌")

            if result["violations"]:
                logger.error("\n❌ Violations:")
                for v in result["violations"]:
                    logger.error("  Line %s: %s - %s", v["line"], v["type"], v["message"])

            if result["warnings"]:
                logger.warning("\n⚠️  Warnings:")
                for w in result["warnings"]:
                    logger.warning("  Line %s: %s - %s", w["line"], w["type"], w["message"])

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
