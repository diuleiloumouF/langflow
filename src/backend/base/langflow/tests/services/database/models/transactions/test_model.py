# 事务模型测试模块
# 测试 TransactionBase 模型的输入序列化逻辑（排除 code 字段等）
import uuid
from datetime import datetime, timezone

import pytest
from langflow.services.database.models.transactions.model import TransactionBase


def test_serialize_inputs_excludes_code_key():
    """Test that the code key is excluded from inputs when serializing."""
    # 测试序列化输入时排除 code 键
    # 创建包含 code 键的 TransactionBase 对象
    transaction = TransactionBase(
        timestamp=datetime.now(timezone.utc),
        vertex_id="test-vertex",
        target_id="test-target",
        inputs={"param1": "value1", "param2": "value2", "code": "print('Hello, world!')"},
        outputs={"result": "success"},
        status="completed",
        flow_id=uuid.uuid4(),
    )

    # Get the serialized inputs（获取序列化后的输入）
    # 获取序列化后的输入
    serialized_inputs = transaction.serialize_inputs(transaction.inputs)

    # Verify that the code key is excluded（验证 code 键被排除）
    # 验证 code 键被排除
    assert "code" not in serialized_inputs
    assert "param1" in serialized_inputs
    assert "param2" in serialized_inputs
    assert serialized_inputs["param1"] == "value1"
    assert serialized_inputs["param2"] == "value2"


def test_serialize_inputs_handles_none():
    """Test that the serialize_inputs method handles None inputs."""
    # 测试 serialize_inputs 方法处理 None 输入
    # 创建具有 None 输入的 TransactionBase 对象
    transaction = TransactionBase(
        timestamp=datetime.now(timezone.utc),
        vertex_id="test-vertex",
        target_id="test-target",
        inputs=None,
        outputs={"result": "success"},
        status="completed",
        flow_id=uuid.uuid4(),
    )

    # Get the serialized inputs（获取序列化后的输入）
    # 获取序列化后的输入
    serialized_inputs = transaction.serialize_inputs(transaction.inputs)

    # Verify that None is returned（验证返回 None）
    # 验证返回 None
    assert serialized_inputs is None


def test_serialize_inputs_handles_non_dict():
    """Test that the serialize_inputs method handles non-dict inputs."""
    # 测试 serialize_inputs 方法处理非字典输入
    # 创建具有有效输入的 TransactionBase 对象
    transaction = TransactionBase(
        timestamp=datetime.now(timezone.utc),
        vertex_id="test-vertex",
        target_id="test-target",
        inputs={},  # Empty dict is valid
        outputs={"result": "success"},
        status="completed",
        flow_id=uuid.uuid4(),
    )

    # Call serialize_inputs directly with a non-dict value（直接使用非字典值调用 serialize_inputs）
    # 直接使用非字典值调用 serialize_inputs
    serialized_inputs = transaction.serialize_inputs("not a dict")

    # Verify that the input is returned as is（验证输入按原样返回）
    # 验证输入按原样返回
    assert serialized_inputs == "not a dict"


def test_serialize_inputs_handles_empty_dict():
    """Test that the serialize_inputs method handles empty dict inputs."""
    # 测试 serialize_inputs 方法处理空字典输入
    # 创建具有空字典输入的 TransactionBase 对象
    transaction = TransactionBase(
        timestamp=datetime.now(timezone.utc),
        vertex_id="test-vertex",
        target_id="test-target",
        inputs={},
        outputs={"result": "success"},
        status="completed",
        flow_id=uuid.uuid4(),
    )

    # Get the serialized inputs（获取序列化后的输入）
    # 获取序列化后的输入
    serialized_inputs = transaction.serialize_inputs(transaction.inputs)

    # Verify that an empty dict is returned（验证返回空字典）
    # 验证返回空字典
    assert serialized_inputs == {}


@pytest.mark.asyncio
async def test_code_key_not_saved_to_database():
    """Test that the code key is not saved to the database."""
    # 测试 code 键不会保存到数据库
    # 创建包含 code 键的输入数据
    input_data = {"param1": "value1", "param2": "value2", "code": "print('Hello, world!')"}

    # Create a transaction with inputs containing a code key
    # 创建包含 code 键输入的事务
    transaction = TransactionBase(
        timestamp=datetime.now(timezone.utc),
        vertex_id="test-vertex",
        target_id="test-target",
        inputs=input_data,
        outputs={"result": "success"},
        status="completed",
        flow_id=uuid.uuid4(),
    )

    # Verify that the code key is removed during transaction creation
    # 验证在事务创建期间 code 键被移除
    assert transaction.inputs is not None
    assert "code" not in transaction.inputs
    assert "param1" in transaction.inputs
    assert "param2" in transaction.inputs

    # Verify that the code key is excluded when serializing
    # 验证序列化时 code 键被排除
    serialized_inputs = transaction.serialize_inputs(transaction.inputs)
    assert "code" not in serialized_inputs
    assert "param1" in serialized_inputs
    assert "param2" in serialized_inputs
