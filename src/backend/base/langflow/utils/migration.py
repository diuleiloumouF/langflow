# 数据库迁移工具函数模块
# 提供检查数据库表、列、外键和约束是否存在的工具函数，
# 用于 Alembic 数据库迁移脚本中
import sqlalchemy as sa


# 检查数据库表是否存在
def table_exists(name, conn):
    """Check if a table exists.

    Parameters:
    name (str): The name of the table to check.
    conn (sqlalchemy.engine.Engine or sqlalchemy.engine.Connection): The SQLAlchemy engine or connection to use.

    Returns:
    bool: True if the table exists, False otherwise.
    """
    inspector = sa.inspect(conn)
    return name in inspector.get_table_names()


# 检查表中是否存在指定列
def column_exists(table_name, column_name, conn):
    """Check if a column exists in a table.

    Parameters:
    table_name (str): The name of the table to check.
    column_name (str): The name of the column to check.
    conn (sqlalchemy.engine.Engine or sqlalchemy.engine.Connection): The SQLAlchemy engine or connection to use.

    Returns:
    bool: True if the column exists, False otherwise.
    """
    inspector = sa.inspect(conn)
    return column_name in [column["name"] for column in inspector.get_columns(table_name)]


# 检查表中是否存在指定外键
def foreign_key_exists(table_name, fk_name, conn):
    """Check if a foreign key exists in a table.

    Parameters:
    table_name (str): The name of the table to check.
    fk_name (str): The name of the foreign key to check.
    conn (sqlalchemy.engine.Engine or sqlalchemy.engine.Connection): The SQLAlchemy engine or connection to use.

    Returns:
    bool: True if the foreign key exists, False otherwise.
    """
    inspector = sa.inspect(conn)
    return fk_name in [fk["name"] for fk in inspector.get_foreign_keys(table_name)]


# 检查表中是否存在指定唯一约束
def constraint_exists(table_name, constraint_name, conn):
    """Check if a constraint exists in a table.

    Parameters:
    table_name (str): The name of the table to check.
    constraint_name (str): The name of the constraint to check.
    conn (sqlalchemy.engine.Engine or sqlalchemy.engine.Connection): The SQLAlchemy engine or connection to use.

    Returns:
    bool: True if the constraint exists, False otherwise.
    """
    inspector = sa.inspect(conn)
    constraints = inspector.get_unique_constraints(table_name)
    return constraint_name in [constraint["name"] for constraint in constraints]
