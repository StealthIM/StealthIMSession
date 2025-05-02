import pytest
import logging
import asyncio
import time
import random
import string
from typing import List, Dict, Optional
import pytest_asyncio
import concurrent.futures
from test_py import SessionClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# pytest-asyncio 配置
pytestmark = pytest.mark.asyncio

# 压力测试配置
CONCURRENT_CLIENTS = 10       # 并发客户端数量
SESSIONS_PER_CLIENT = 100     # 每个客户端创建的会话数
OPERATION_ROUNDS = 3          # 操作轮次
DELETE_PROBABILITY = 0.3      # 删除会话的概率


@pytest_asyncio.fixture
async def stress_clients():
    """创建多个测试客户端的fixture"""
    clients = []
    for i in range(CONCURRENT_CLIENTS):
        client = SessionClient()
        await client.connect()
        clients.append(client)

    await asyncio.sleep(1)  # 等待所有连接建立
    yield clients

    # 清理所有客户端连接
    for client in clients:
        await client.disconnect()


async def create_session(client: SessionClient, uid: int) -> Optional[str]:
    """创建会话并返回会话ID"""
    try:
        result = await client.set_session(uid)
        if result[0] == 0 and result[1]:
            return result[1]
        return None
    except Exception as e:
        logger.error(f"创建会话失败: {e}")
        return None


async def get_session(client: SessionClient, session_id: str) -> bool:
    """获取会话信息"""
    try:
        result = await client.get_session(session_id)
        return result[0] == 0
    except Exception as e:
        logger.error(f"获取会话失败: {e}")
        return False


async def delete_session(client: SessionClient, session_id: str) -> bool:
    """删除会话"""
    try:
        result = await client.delete_session(session_id)
        return result == 0
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        return False


async def run_client_workload(client_id: int, client: SessionClient):
    """为单个客户端运行工作负载"""
    logger.info(f"客户端 {client_id} 开始工作负载")
    sessions: Dict[str, int] = {}  # 会话ID到UID的映射

    # 创建会话阶段
    for i in range(SESSIONS_PER_CLIENT):
        uid = random.randint(1, 1000000)
        session_id = await create_session(client, uid)
        if session_id:
            sessions[session_id] = uid
            if i % 20 == 0:  # 每20个会话记录一次日志
                logger.info(
                    f"客户端 {client_id} 已创建 {i+1}/{SESSIONS_PER_CLIENT} 个会话")

    logger.info(f"客户端 {client_id} 完成会话创建，共 {len(sessions)} 个会话")

    # 随机访问和删除会话
    active_sessions = list(sessions.keys())
    for round in range(OPERATION_ROUNDS):
        if not active_sessions:
            break

        logger.info(f"客户端 {client_id} 开始第 {round+1}/{OPERATION_ROUNDS} 轮操作")
        operations = []

        # 随机选择会话进行操作
        sample_size = min(len(active_sessions), max(
            10, len(active_sessions) // 2))
        selected_sessions = random.sample(active_sessions, sample_size)

        for session_id in selected_sessions:
            # 有一定概率删除会话
            if random.random() < DELETE_PROBABILITY:
                operations.append(delete_session(client, session_id))
                active_sessions.remove(session_id)
            else:
                # 否则获取会话
                operations.append(get_session(client, session_id))

        # 等待所有操作完成
        results = await asyncio.gather(*operations)
        success = results.count(True)
        logger.info(
            f"客户端 {client_id} 第 {round+1} 轮: {success}/{len(operations)} 操作成功")

    return len(sessions), len(active_sessions)


@pytest.mark.asyncio
async def test_memory_stress(stress_clients):
    """测试服务在高内存压力下的性能"""
    start_time = time.time()

    # 启动所有客户端的工作负载
    tasks = []
    for i, client in enumerate(stress_clients):
        tasks.append(run_client_workload(i, client))

    # 等待所有工作负载完成
    results = await asyncio.gather(*tasks)

    # 统计结果
    total_sessions = sum(created for created, _ in results)
    remaining_sessions = sum(remaining for _, remaining in results)
    duration = time.time() - start_time

    logger.info(f"内存压力测试完成:")
    logger.info(f"- 总计创建会话数: {total_sessions}")
    logger.info(f"- 未删除会话数: {remaining_sessions}")
    logger.info(f"- 总执行时间: {duration:.2f} 秒")
    logger.info(f"- 每秒平均处理会话: {total_sessions/duration:.2f}")

    # 测试断言
    assert total_sessions > 0, "应该成功创建至少一些会话"
    assert duration > 0, "测试时间应该为正值"


@pytest.mark.asyncio
async def test_concurrent_same_uid(stress_clients):
    """测试多个客户端并发访问同一个UID的会话"""
    # 使用相同的UID
    shared_uid = 12345
    session_ids = []

    # 所有客户端并发地为同一个UID创建会话
    create_tasks = []
    for client in stress_clients:
        create_tasks.append(create_session(client, shared_uid))

    session_ids = await asyncio.gather(*create_tasks)
    valid_sessions = [s for s in session_ids if s]

    logger.info(f"为共享UID {shared_uid} 创建了 {len(valid_sessions)} 个会话")

    # 所有客户端并发获取所有会话
    total_get_operations = 0
    success_get_operations = 0

    for session_id in valid_sessions:
        get_tasks = []
        for client in stress_clients:
            get_tasks.append(get_session(client, session_id))

        results = await asyncio.gather(*get_tasks)
        total_get_operations += len(results)
        success_get_operations += results.count(True)

    # 所有客户端并发删除会话
    total_delete_operations = 0
    success_delete_operations = 0

    for session_id in valid_sessions:
        # 随机选择一个客户端删除会话
        client = random.choice(stress_clients)
        result = await delete_session(client, session_id)
        total_delete_operations += 1
        if result:
            success_delete_operations += 1

    logger.info(f"并发同UID测试完成:")
    logger.info(f"- 有效会话数: {len(valid_sessions)}")
    logger.info(f"- 获取操作: {success_get_operations}/{total_get_operations} 成功")
    logger.info(
        f"- 删除操作: {success_delete_operations}/{total_delete_operations} 成功")

    # 测试断言
    assert len(valid_sessions) > 0, "应该成功创建至少一些会话"
    assert success_get_operations > 0, "应该成功获取至少一些会话"


@pytest.mark.asyncio
async def test_rapid_create_delete_cycle():
    """测试快速创建和删除会话的循环"""
    client = SessionClient()
    await client.connect()

    try:
        cycle_count = 200
        success_count = 0

        start_time = time.time()

        for i in range(cycle_count):
            uid = random.randint(1, 1000000)
            result = await client.set_session(uid)

            if result[0] == 0 and result[1]:
                session_id = result[1]
                delete_result = await client.delete_session(session_id)

                if delete_result == 0:
                    success_count += 1

            if i % 50 == 0:
                logger.info(f"已完成 {i}/{cycle_count} 个创建/删除循环")

        duration = time.time() - start_time

        logger.info(f"快速创建/删除循环测试完成:")
        logger.info(f"- 成功循环: {success_count}/{cycle_count}")
        logger.info(f"- 总执行时间: {duration:.2f} 秒")
        logger.info(f"- 每秒平均循环: {cycle_count/duration:.2f}")

        assert success_count > 0, "应该成功执行至少一些创建/删除循环"

    finally:
        await client.disconnect()


if __name__ == "__main__":
    pytest.main(["-v", "test_memory_stress.py"])
