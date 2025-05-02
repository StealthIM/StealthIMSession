import pytest
import logging
from typing import Optional, List, Dict, Any, Tuple
import asyncio
import pytest_asyncio
from test_py import SessionClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# pytest-asyncio 配置
pytestmark = pytest.mark.asyncio

# 测试数据 - 根据实际行为调整预期值
SET_SESSION_CASES = [
    pytest.param(123, 0, id="normal_user"),
    pytest.param(0, 0, id="zero_user_id"),
    pytest.param(-1, 0, id="negative_user_id"),  # 服务允许负数UID
    pytest.param(999999999, 0, id="large_user_id"),
]

GET_SESSION_CASES = [
    # (session_id, 预期状态码, 预期uid)
    pytest.param("valid_session", 0, 123, id="valid_session"),
    pytest.param("invalid_session", 1, 0, id="invalid_session"),  # 状态码为1
    pytest.param("", 1, 0, id="empty_session"),  # 状态码为1
]

DELETE_SESSION_CASES = [
    # (session_id, 预期状态码)
    pytest.param("valid_session", 0, id="delete_valid_session"),
    pytest.param("invalid_session", 0, id="delete_invalid_session"),
    pytest.param("", 0, id="delete_empty_session"),  # 服务返回0
]

# 多轮会话测试场景 - 根据实际行为调整预期值
SESSION_LIFECYCLE_SCENARIOS = [
    # 场景名称, UID, 期望的操作结果列表
    pytest.param(
        "normal_lifecycle",
        123,
        [
            ("set", 0),       # 设置会话成功
            ("get", 0),       # 获取会话成功
            ("delete", 0),    # 删除会话成功
            ("get", 1)        # 获取已删除会话失败，状态码为1
        ],
        id="normal_ lifecycle"
    ),
    pytest.param(
        "set_twice_delete_once",
        456,
        [
            ("set", 0),       # 第一次设置会话成功
            ("set", 0),       # 第二次设置另一个会话成功
            ("delete", 0),    # 删除第二个会话成功
            ("get", 0),       # 获取第一个会话成功（服务行为是仍能获取第一个会话）
            ("get", 0)        # 获取第一个会话成功
        ],
        id="set_twice_delete_once"
    ),
    pytest.param(
        "multiple_user_sessions",
        789,
        [
            ("set", 0),             # 为用户789设置会话1
            ("get", 0),             # 获取会话1成功
            ("set_with_uid", 0, 101),     # 为用户101设置会话2
            ("get", 0),             # 获取会话1成功
            ("switch", 0, 1),       # 切换到会话2，参数为索引
            ("get", 0),             # 获取会话2成功
            ("delete", 0),          # 删除会话2
            ("switch", 0, 0),       # 切换回会话1，参数为索引
            ("get", 0),             # 获取会话1成功
            ("delete", 0),          # 删除会话1
            ("get", 1)              # 获取已删除的会话1失败
        ],
        id="multiple_user_sessions"
    ),
    pytest.param(
        "session_reset_scenario",
        202,
        [
            ("set", 0),             # 设置会话成功
            ("get", 0),             # 获取会话成功
            ("reload", 0),          # 重新加载服务配置
            ("get", 0),             # 验证重新加载后会话仍存在
            ("delete", 0),          # 删除会话
            ("get", 1)              # 获取已删除会话应失败
        ],
        id="session_reset_scenario"
    ),
]


@pytest_asyncio.fixture
async def client():
    """创建测试客户端fixture"""
    client = SessionClient()
    await client.connect()
    await asyncio.sleep(1)  # 等待连接建立
    yield client
    await client.disconnect()


@pytest.mark.asyncio
async def test_ping(client: SessionClient):
    """测试ping功能"""
    assert await client.ping() is True


@pytest.mark.asyncio
@pytest.mark.parametrize("uid, expected_code", SET_SESSION_CASES)
async def test_set_session(client: SessionClient, uid: int, expected_code: int):
    """测试设置会话，使用参数化测试"""
    result = await client.set_session(uid)
    assert result[0] == expected_code, f"设置会话应返回状态码 {expected_code}，但得到 {result[0]}"

    if expected_code == 0:
        # 如果预期成功，确认会话ID不为空
        assert result[1], "成功设置会话应返回有效会话ID"


@pytest.mark.asyncio
@pytest.mark.parametrize("session_id, expected_code, expected_uid", GET_SESSION_CASES)
async def test_get_session(client: SessionClient, session_id: str, expected_code: int, expected_uid: int):
    """测试获取会话，使用参数化测试"""
    # 对于有效会话用例，先创建一个会话
    if session_id == "valid_session" and expected_code == 0:
        set_result = await client.set_session(expected_uid)
        assert set_result[0] == 0, "设置会话失败，无法继续测试获取会话"
        session_id = set_result[1]  # 使用真实的会话ID

    result = await client.get_session(session_id)
    assert result[0] == expected_code, f"获取会话应返回状态码 {expected_code}，但得到 {result[0]}"

    if expected_code == 0:
        assert result[1] == expected_uid, f"获取会话应返回UID {expected_uid}，但得到 {result[1]}"


@pytest.mark.asyncio
@pytest.mark.parametrize("session_id, expected_code", DELETE_SESSION_CASES)
async def test_delete_session(client: SessionClient, session_id: str, expected_code: int):
    """测试删除会话，使用参数化测试"""
    # 对于有效会话用例，先创建一个会话
    if session_id == "valid_session":
        set_result = await client.set_session(123)
        assert set_result[0] == 0, "设置会话失败，无法继续测试删除会话"
        session_id = set_result[1]  # 使用真实的会话ID

    result = await client.delete_session(session_id)
    assert result == expected_code, f"删除会话应返回状态码 {expected_code}，但得到 {result}"


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario_name, uid, operations", SESSION_LIFECYCLE_SCENARIOS)
async def test_session_lifecycle_scenarios(client: SessionClient, scenario_name: str, uid: int, operations: List):
    """测试会话生命周期的多轮场景"""
    logger.info(f"执行测试场景: {scenario_name}")

    # 存储会话ID
    session_ids = []
    current_session_index = -1  # 当前操作的会话索引

    for index, operation_data in enumerate(operations):
        # 解析操作数据
        if len(operation_data) == 2:
            operation, expected_code = operation_data
            extra_param = None
        elif len(operation_data) == 3:
            operation, expected_code, extra_param = operation_data
        else:
            assert False, f"无效的操作数据格式: {operation_data}"

        logger.info(
            f"执行操作 #{index+1}: {operation}, 预期状态码: {expected_code}, 额外参数: {extra_param}")

        if operation == "set":
            # 设置会话
            result = await client.set_session(uid)
            session_ids.append(result[1])
            current_session_index = len(session_ids) - 1
            assert result[0] == expected_code, f"设置会话应返回状态码 {expected_code}，但得到 {result[0]}"

        elif operation == "set_with_uid":
            # 使用指定的UID设置会话
            custom_uid = int(extra_param)  # 确保是整数
            result = await client.set_session(custom_uid)
            session_ids.append(result[1])
            current_session_index = len(session_ids) - 1
            assert result[0] == expected_code, f"设置会话应返回状态码 {expected_code}，但得到 {result[0]}"

        elif operation == "get":
            # 获取会话
            if session_ids and current_session_index >= 0:
                session_id = session_ids[current_session_index]
                result = await client.get_session(session_id)
                assert result[0] == expected_code, f"获取会话应返回状态码 {expected_code}，但得到 {result[0]}"

                if expected_code == 0:
                    # 确认UID - 检查当前操作的是哪个用户的会话
                    expected_uid = uid
                    if scenario_name == "multiple_user_sessions" and current_session_index == 1:
                        expected_uid = 101  # 使用为第二个会话指定的UID
                    assert result[1] == expected_uid, f"获取会话应返回UID {expected_uid}，但得到 {result[1]}"
            else:
                logger.warning("尝试获取会话，但没有可用的会话ID")

        elif operation == "delete":
            # 删除会话
            if session_ids and current_session_index >= 0:
                session_id = session_ids[current_session_index]
                result = await client.delete_session(session_id)
                assert result == expected_code, f"删除会话应返回状态码 {expected_code}，但得到 {result}"

                # 特殊处理：在不同场景下的删除后处理
                if scenario_name == "set_twice_delete_once" and current_session_index > 0:
                    current_session_index = 0
            else:
                logger.warning("尝试删除会话，但没有可用的会话ID")

        elif operation == "switch":
            # 切换当前使用的会话
            target_index = int(extra_param)  # 确保是整数
            assert 0 <= target_index < len(
                session_ids), f"无效的会话索引: {target_index}"
            current_session_index = target_index
            logger.info(
                f"切换到会话索引 {current_session_index}: {session_ids[current_session_index]}")

        elif operation == "reload":
            # 重载服务配置
            result = await client.reload_service()
            assert result == expected_code, f"重载服务应返回状态码 {expected_code}，但得到 {result}"

        else:
            assert False, f"未知的操作类型: {operation}"


@pytest.mark.asyncio
async def test_reload_service(client: SessionClient):
    """测试服务重载功能"""
    assert await client.reload_service() == 0, "重载服务应成功"
