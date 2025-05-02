#!/usr/bin/env python
import asyncio
import argparse
import logging
import time
import statistics
import sys
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
from test_py import SessionClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            f'service_diagnostics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("diagnostics")

# 诊断结果存储
results = {
    "latency": {
        "set": [],
        "get": [],
        "del": [],
        "ping": []
    },
    "errors": {
        "set": [],
        "get": [],
        "del": [],
        "ping": []
    },
    "success_rate": {
        "set": 0,
        "get": 0,
        "del": 0,
        "ping": 0
    },
    "test_conditions": {},
    "verdict": ""
}


async def measure_operation(client: SessionClient, operation: str, *args, **kwargs) -> Tuple[float, Any, bool]:
    """测量操作延迟和结果"""
    start_time = time.time()
    success = False
    error_msg = None

    try:
        if operation == "ping":
            result = await client.ping()
            success = result is True
        elif operation == "set":
            uid = args[0] if args else kwargs.get("uid", 12345)
            result = await client.set_session(uid)
            success = result[0] == 0
        elif operation == "get":
            session_id = args[0] if args else kwargs.get("session_id", "")
            result = await client.get_session(session_id)
            success = result[0] == 0
        elif operation == "del":
            session_id = args[0] if args else kwargs.get("session_id", "")
            result = await client.delete_session(session_id)
            success = result == 0
        else:
            raise ValueError(f"未知操作: {operation}")

    except Exception as e:
        result = None
        error_msg = str(e)
        logger.error(f"操作 {operation} 出错: {e}")

    latency = time.time() - start_time

    return latency, result, success, error_msg


async def run_latency_test(client: SessionClient, operation_count: int = 50):
    """运行延迟测试"""
    logger.info(f"开始延迟测试 - 每个操作执行 {operation_count} 次")

    # 测试 ping 延迟
    for i in range(operation_count):
        latency, _, success, error = await measure_operation(client, "ping")
        results["latency"]["ping"].append(latency)
        if not success and error:
            results["errors"]["ping"].append(error)

    ping_success_rate = 1 - (len(results["errors"]["ping"]) / operation_count)
    results["success_rate"]["ping"] = ping_success_rate

    logger.info(f"Ping 延迟: avg={statistics.mean(results['latency']['ping']):.4f}s, "
                f"min={min(results['latency']['ping']):.4f}s, "
                f"max={max(results['latency']['ping']):.4f}s, "
                f"成功率: {ping_success_rate*100:.1f}%")

    # 测试 set 操作延迟和成功率
    session_ids = []
    for i in range(operation_count):
        uid = 10000 + i
        latency, result, success, error = await measure_operation(client, "set", uid)
        results["latency"]["set"].append(latency)
        if success:
            session_ids.append(result[1])
        elif error:
            results["errors"]["set"].append(error)

    set_success_rate = len(session_ids) / operation_count
    results["success_rate"]["set"] = set_success_rate

    logger.info(f"Set 延迟: avg={statistics.mean(results['latency']['set']):.4f}s, "
                f"min={min(results['latency']['set']):.4f}s, "
                f"max={max(results['latency']['set']):.4f}s, "
                f"成功率: {set_success_rate*100:.1f}%")

    # 测试 get 操作延迟和成功率
    if session_ids:
        for session_id in session_ids[:min(operation_count, len(session_ids))]:
            latency, _, success, error = await measure_operation(client, "get", session_id)
            results["latency"]["get"].append(latency)
            if not success and error:
                results["errors"]["get"].append(error)

        get_success_rate = 1 - (len(results["errors"]["get"]) / len(
            results["latency"]["get"]) if results["latency"]["get"] else 0)
        results["success_rate"]["get"] = get_success_rate

        if results["latency"]["get"]:
            logger.info(f"Get 延迟: avg={statistics.mean(results['latency']['get']):.4f}s, "
                        f"min={min(results['latency']['get']):.4f}s, "
                        f"max={max(results['latency']['get']):.4f}s, "
                        f"成功率: {get_success_rate*100:.1f}%")

    # 测试 delete 操作延迟和成功率
    if session_ids:
        for session_id in session_ids[:min(operation_count, len(session_ids))]:
            latency, _, success, error = await measure_operation(client, "del", session_id)
            results["latency"]["del"].append(latency)
            if not success and error:
                results["errors"]["del"].append(error)

        del_success_rate = 1 - (len(results["errors"]["del"]) / len(
            results["latency"]["del"]) if results["latency"]["del"] else 0)
        results["success_rate"]["del"] = del_success_rate

        if results["latency"]["del"]:
            logger.info(f"Delete 延迟: avg={statistics.mean(results['latency']['del']):.4f}s, "
                        f"min={min(results['latency']['del']):.4f}s, "
                        f"max={max(results['latency']['del']):.4f}s, "
                        f"成功率: {del_success_rate*100:.1f}%")


async def run_error_patterns_test(client: SessionClient, iterations: int = 20):
    """测试不同操作的错误模式"""
    logger.info("开始错误模式测试")

    # 测试无效会话ID
    invalid_session_errors = []
    for i in range(iterations):
        invalid_id = f"invalid_session_{i}"
        _, _, success, error = await measure_operation(client, "get", invalid_id)
        if not success and error:
            invalid_session_errors.append(error)

    # 测试连续多次删除同一会话
    if results["success_rate"]["set"] > 0:
        # 创建一个会话
        _, result, success, _ = await measure_operation(client, "set", 99999)
        if success:
            session_id = result[1]

            # 第一次删除
            _, _, first_del_success, _ = await measure_operation(client, "del", session_id)

            # 尝试再次删除同一会话
            multiple_delete_errors = []
            for i in range(3):
                _, _, success, error = await measure_operation(client, "del", session_id)
                if not success and error:
                    multiple_delete_errors.append(error)

            logger.info(f"重复删除同一会话: 初次删除成功率: {100 if first_del_success else 0}%, "
                        f"重复删除错误数: {len(multiple_delete_errors)}")

    # 测试特殊字符会话ID
    special_chars = ["", " ", "'", "\"", ";", "<script>", None]
    special_id_errors = []

    for special_id in special_chars:
        if special_id is not None:  # None会导致类型错误，实际测试中我们跳过
            _, _, success, error = await measure_operation(client, "get", special_id)
            if not success and error:
                special_id_errors.append((special_id, error))

    logger.info(f"特殊字符会话ID错误数: {len(special_id_errors)}")

    # 测试极限UID值
    extreme_uids = [0, -1, 2**31-1, 2**31, 2**63-1]
    extreme_uid_results = []

    for uid in extreme_uids:
        latency, result, success, error = await measure_operation(client, "set", uid)
        status = "成功" if success else "失败"
        error_msg = error if error else "无"
        extreme_uid_results.append((uid, status, error_msg))

        # 如果成功创建了会话，尝试删除它
        if success and result and isinstance(result, tuple) and len(result) > 1:
            await measure_operation(client, "del", result[1])

    logger.info(f"极限UID值测试完成，结果数: {len(extreme_uid_results)}")


async def run_concurrency_test(client: SessionClient, concurrency: int = 20):
    """测试并发操作的响应情况"""
    logger.info(f"开始并发测试 - 并发等级: {concurrency}")

    # 创建一批会话
    session_ids = []
    for i in range(concurrency):
        uid = 20000 + i
        _, result, success, _ = await measure_operation(client, "set", uid)
        if success:
            session_ids.append(result[1])

    if not session_ids:
        logger.warning("没有成功创建会话，跳过并发测试")
        return

    # 并发获取会话
    start_time = time.time()
    get_tasks = []

    for i in range(concurrency):
        # 随机选择一个会话ID
        session_id = session_ids[i % len(session_ids)]
        get_tasks.append(measure_operation(client, "get", session_id))

    get_results = await asyncio.gather(*get_tasks)
    get_latencies = [r[0] for r in get_results]
    get_success_count = sum(1 for r in get_results if r[2])

    logger.info(f"并发获取会话: 成功率: {get_success_count / concurrency * 100:.1f}%, "
                f"平均延迟: {statistics.mean(get_latencies):.4f}s, "
                f"最大延迟: {max(get_latencies):.4f}s")

    # 并发删除会话
    del_tasks = []

    for i in range(min(concurrency, len(session_ids))):
        del_tasks.append(measure_operation(client, "del", session_ids[i]))

    del_results = await asyncio.gather(*del_tasks)
    del_latencies = [r[0] for r in del_results]
    del_success_count = sum(1 for r in del_results if r[2])

    logger.info(f"并发删除会话: 成功率: {del_success_count / len(del_tasks) * 100:.1f}%, "
                f"平均延迟: {statistics.mean(del_latencies):.4f}s, "
                f"最大延迟: {max(del_latencies):.4f}s")


async def analyze_results():
    """分析测试结果，判断问题来源"""
    logger.info("分析测试结果...")

    # 延迟分析
    high_latency = False
    latency_variance = False

    for op, latencies in results["latency"].items():
        if latencies:
            avg_latency = statistics.mean(latencies)
            if avg_latency > 0.5:  # 如果平均延迟超过500毫秒
                high_latency = True
                logger.warning(f"操作 {op} 的平均延迟较高: {avg_latency:.4f}s")

            if len(latencies) > 5:
                stdev = statistics.stdev(latencies)
                if stdev > avg_latency * 0.5:  # 如果标准差大于平均值的50%
                    latency_variance = True
                    logger.warning(
                        f"操作 {op} 的延迟波动较大: 平均值 {avg_latency:.4f}s, 标准差 {stdev:.4f}s")

    # 成功率分析
    low_success_rate = False
    for op, rate in results["success_rate"].items():
        if rate < 0.95:  # 如果成功率低于95%
            low_success_rate = True
            logger.warning(f"操作 {op} 的成功率较低: {rate*100:.1f}%")

    # 错误模式分析
    error_pattern_exists = False
    for op, errors in results["errors"].items():
        if errors:
            error_pattern_exists = True
            logger.warning(f"操作 {op} 发生了 {len(errors)} 个错误")
            # 分析前5个错误
            for i, err in enumerate(errors[:5]):
                logger.warning(f"  错误 {i+1}: {err}")

    # 综合判断
    if high_latency and latency_variance and low_success_rate:
        verdict = "服务端问题: 高延迟、波动大且成功率低，可能是服务过载或资源不足"
    elif high_latency and not latency_variance:
        verdict = "网络问题: 高延迟但波动小，可能是网络延迟或服务端处理时间长但稳定"
    elif low_success_rate and error_pattern_exists:
        verdict = "服务端问题: 成功率低且有明确错误模式，服务可能存在逻辑或资源问题"
    elif latency_variance and not high_latency:
        verdict = "服务端问题: 延迟波动大但平均延迟正常，服务可能存在竞争条件或资源争用"
    elif not high_latency and not latency_variance and not low_success_rate:
        verdict = "测试端问题: 服务表现良好，问题可能出在测试方法或测试环境中"
    else:
        verdict = "无法确定: 需要更多数据来判断问题源头"

    results["verdict"] = verdict
    logger.info(f"诊断结论: {verdict}")

    # 将结果保存到JSON文件
    with open(f"diagnostics_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info("诊断结果已保存到JSON文件")


async def run_diagnostics(host: str = '127.0.0.1', port: int = 50054):
    """运行全面诊断测试"""
    logger.info(f"开始服务诊断 - 连接到 {host}:{port}")
    results["test_conditions"] = {
        "host": host,
        "port": port,
        "timestamp": datetime.now().isoformat(),
    }

    client = SessionClient(host, port)

    try:
        await client.connect()
        logger.info("连接到服务成功")

        # 运行延迟测试
        await run_latency_test(client)

        # 运行错误模式测试
        await run_error_patterns_test(client)

        # 运行并发测试
        await run_concurrency_test(client)

        # 分析结果
        await analyze_results()

    except Exception as e:
        logger.error(f"诊断过程中发生错误: {e}")
        results["verdict"] = f"测试失败: {str(e)}"
    finally:
        await client.disconnect()
        logger.info("诊断完成")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StealthIM Session 服务诊断工具")
    parser.add_argument("--host", default="127.0.0.1",
                        help="服务主机地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=50054,
                        help="服务端口 (默认: 50054)")

    args = parser.parse_args()

    asyncio.run(run_diagnostics(args.host, args.port))
