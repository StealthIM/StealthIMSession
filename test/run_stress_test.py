#!/usr/bin/env python
import argparse
import asyncio
import logging
import time
import sys
from test_py import SessionClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('stress_test_results.log')
    ]
)
logger = logging.getLogger("stress_test")


async def run_stress_test(client_count: int, sessions_per_client: int,
                          batch_size: int = 10, sleep_between_batches: float = 0.1):
    """运行内存压力测试"""
    logger.info(f"开始内存压力测试: {client_count} 客户端, 每客户端 {sessions_per_client} 会话")

    # 创建客户端
    clients = []
    for i in range(client_count):
        client = SessionClient()
        await client.connect()
        clients.append(client)
        logger.info(f"客户端 {i+1}/{client_count} 连接成功")

    try:
        start_time = time.time()
        total_sessions = 0
        success_sessions = 0

        # 为每个客户端创建会话
        for client_idx, client in enumerate(clients):
            logger.info(f"客户端 {client_idx+1} 开始创建会话")
            client_success = 0

            # 分批创建会话以减轻服务器压力
            for batch_start in range(0, sessions_per_client, batch_size):
                batch_end = min(batch_start + batch_size, sessions_per_client)
                batch_size_actual = batch_end - batch_start

                tasks = []
                for i in range(batch_size_actual):
                    session_idx = batch_start + i
                    uid = 10000 * client_idx + session_idx  # 确保UID唯一
                    tasks.append(client.set_session(uid))

                # 执行批量创建
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 统计成功数
                for result in results:
                    total_sessions += 1
                    if isinstance(result, tuple) and result[0] == 0:
                        success_sessions += 1
                        client_success += 1

                # 记录进度并暂停一下，避免请求过于密集
                logger.info(
                    f"客户端 {client_idx+1} - 已创建 {batch_end}/{sessions_per_client} 会话")
                await asyncio.sleep(sleep_between_batches)

            logger.info(
                f"客户端 {client_idx+1} 完成 - 成功率: {client_success}/{sessions_per_client}")

        duration = time.time() - start_time

        # 输出总体统计
        logger.info("=" * 50)
        logger.info("内存压力测试完成")
        logger.info(f"总会话数: {total_sessions}")
        logger.info(f"成功会话数: {success_sessions}")
        logger.info(f"成功率: {success_sessions/total_sessions*100:.2f}%")
        logger.info(f"总时间: {duration:.2f} 秒")
        logger.info(f"每秒会话创建: {total_sessions/duration:.2f}")
        logger.info("=" * 50)

    finally:
        # 关闭所有客户端连接
        logger.info("关闭客户端连接...")
        for client in clients:
            await client.disconnect()


async def memory_leak_test(hours: float = 1.0, check_interval: int = 300):
    """长时间运行以检测内存泄漏"""
    logger.info(f"开始内存泄漏测试，计划运行 {hours} 小时")

    client = SessionClient()
    await client.connect()

    try:
        end_time = time.time() + hours * 3600
        check_count = 0
        active_sessions = {}  # 会话ID -> 创建时间

        while time.time() < end_time:
            check_count += 1
            logger.info(
                f"检查点 #{check_count} - 已运行 {(time.time() - (end_time - hours * 3600))/3600:.2f} 小时")

            # 创建一些新会话
            new_sessions = 10
            for i in range(new_sessions):
                uid = int(time.time() * 1000) % 1000000 + i
                result = await client.set_session(uid)
                if result[0] == 0 and result[1]:
                    active_sessions[result[1]] = time.time()

            # 获取一些现有会话
            if active_sessions:
                sessions_to_check = min(20, len(active_sessions))
                session_ids = list(active_sessions.keys())[-sessions_to_check:]

                for session_id in session_ids:
                    await client.get_session(session_id)

            # 删除一些旧会话
            if len(active_sessions) > 100:  # 保持会话数在100以内
                sessions_to_delete = sorted(
                    active_sessions.items(), key=lambda x: x[1])[:20]
                for session_id, _ in sessions_to_delete:
                    await client.delete_session(session_id)
                    active_sessions.pop(session_id, None)

            logger.info(f"活跃会话数: {len(active_sessions)}")

            # 等待下一个检查时间
            await asyncio.sleep(check_interval)

        logger.info(f"内存泄漏测试完成，运行时间: {hours} 小时")

    finally:
        # 清理会话和连接
        logger.info("清理所有活跃会话...")
        for session_id in list(active_sessions.keys()):
            await client.delete_session(session_id)

        await client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StealthIM Session 服务压力测试工具")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 内存压力测试命令
    stress_parser = subparsers.add_parser("stress", help="内存压力测试")
    stress_parser.add_argument("-c", "--clients", type=int, default=5,
                               help="并发客户端数量 (默认: 5)")
    stress_parser.add_argument("-s", "--sessions", type=int, default=100,
                               help="每个客户端创建的会话数 (默认: 100)")
    stress_parser.add_argument("-b", "--batch", type=int, default=10,
                               help="批量创建的会话数 (默认: 10)")
    stress_parser.add_argument("--sleep", type=float, default=0.1,
                               help="批次间暂停时间(秒) (默认: 0.1)")

    # 内存泄漏测试命令
    leak_parser = subparsers.add_parser("leak", help="内存泄漏测试")
    leak_parser.add_argument("-t", "--hours", type=float, default=1.0,
                             help="测试运行时间(小时) (默认: 1.0)")
    leak_parser.add_argument("-i", "--interval", type=int, default=300,
                             help="检查间隔(秒) (默认: 300)")

    args = parser.parse_args()

    if args.command == "stress":
        asyncio.run(run_stress_test(
            client_count=args.clients,
            sessions_per_client=args.sessions,
            batch_size=args.batch,
            sleep_between_batches=args.sleep
        ))
    elif args.command == "leak":
        asyncio.run(memory_leak_test(
            hours=args.hours,
            check_interval=args.interval
        ))
    else:
        parser.print_help()
