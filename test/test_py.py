import asyncio
import logging
from typing import Tuple, Optional, Any, Dict, List

import grpclib.client
from grpclib.exceptions import GRPCError

# 导入生成的protobuf模块
import session_pb2
import session_grpc

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SessionClient:
    """StealthIMSession服务的测试客户端"""

    def __init__(self, host: str = "localhost", port: int = 50054):
        """初始化会话客户端

        Args:
            host: 服务主机名
            port: 服务端口
        """
        self.host = host
        self.port = port
        self.channel = None
        self.session_id = None  # 存储当前会话ID

    async def connect(self) -> None:
        """连接到服务"""
        try:
            self.channel = grpclib.client.Channel(self.host, self.port)
            logger.info(f"已连接到 {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"连接失败: {e}")
            raise

    async def disconnect(self) -> None:
        """断开与服务的连接"""
        if self.channel:
            self.channel.close()
            logger.info("已断开连接")

    async def ping(self) -> bool:
        """测试服务可用性

        Returns:
            bool: 服务是否可用
        """
        try:
            async with self.channel as channel:
                request = session_pb2.PingRequest()
                stub = session_grpc.StealthIMSessionStub(channel)
                response = await stub.Ping(request)
                logger.debug("Ping成功")
                return True
        except Exception as e:
            logger.error(f"Ping失败: {e}")
            return False

    async def set_session(self, uid: int) -> Tuple[int, str]:
        """设置会话

        Args:
            uid: 用户ID

        Returns:
            Tuple[int, str]: (状态码, 会话ID)
        """
        try:

            async with self.channel as channel:
                stub = session_grpc.StealthIMSessionStub(channel)
                request = session_pb2.SetRequest(uid=uid)
                response = await stub.Set(request)

            code = response.result.code
            session = response.session

            if code == 0:
                self.session_id = session  # 存储会话ID
                logger.info(f"设置会话成功: UID={uid}, 会话ID={session}")
            else:
                logger.warning(
                    f"设置会话失败: UID={uid}, 状态码={code}, 信息={response.result.msg}")

            return (code, session)
        except GRPCError as e:
            logger.error(f"设置会话时发生gRPC错误: {e}")
            return (e.status, "")
        except Exception as e:
            logger.error(f"设置会话时发生异常: {e}")
            return (-1, "")

    async def get_session(self, session_id: str) -> Tuple[int, int]:
        """获取会话

        Args:
            session_id: 会话ID

        Returns:
            Tuple[int, int]: (状态码, 用户ID)
        """
        try:
            async with self.channel as channel:
                stub = session_grpc.StealthIMSessionStub(channel)
                request = session_pb2.GetRequest(session=session_id)
                response = await stub.Get(request)

            code = response.result.code
            uid = response.uid

            if code == 0:
                logger.info(f"获取会话成功: 会话ID={session_id}, UID={uid}")
            else:
                logger.warning(
                    f"获取会话失败: 会话ID={session_id}, 状态码={code}, 信息={response.result.msg}")

            return (code, uid)
        except GRPCError as e:
            logger.error(f"获取会话时发生gRPC错误: {e}")
            return (e.status, 0)
        except Exception as e:
            logger.error(f"获取会话时发生异常: {e}")
            return (-1, 0)

    async def delete_session(self, session_id: str) -> int:
        """删除会话

        Args:
            session_id: 会话ID

        Returns:
            int: 状态码
        """
        try:
            async with self.channel as channel:
                stub = session_grpc.StealthIMSessionStub(channel)
                request = session_pb2.DelRequest(session=session_id)
                response = await stub.Del(request)

            code = response.result.code

            if code == 0:
                logger.info(f"删除会话成功: 会话ID={session_id}")
                # 如果删除的是当前会话，清除存储的会话ID
                if session_id == self.session_id:
                    self.session_id = None
            else:
                logger.warning(
                    f"删除会话失败: 会话ID={session_id}, 状态码={code}, 信息={response.result.msg}")

            return code
        except GRPCError as e:
            logger.error(f"删除会话时发生gRPC错误: {e}")
            return e.status
        except Exception as e:
            logger.error(f"删除会话时发生异常: {e}")
            return -1

    async def reload_service(self) -> int:
        """重新加载服务配置

        Returns:
            int: 状态码
        """
        try:
            async with self.channel as channel:
                stub = session_grpc.StealthIMSessionStub(channel)
                request = session_pb2.ReloadRequest()
                response = await stub.Reload(request)

            code = response.result.code

            if code == 0:
                logger.info("重新加载服务配置成功")
            else:
                logger.warning(
                    f"重新加载服务配置失败: 状态码={code}, 信息={response.result.msg}")

            return code
        except GRPCError as e:
            logger.error(f"重新加载服务配置时发生gRPC错误: {e}")
            return e.status
        except Exception as e:
            logger.error(f"重新加载服务配置时发生异常: {e}")
            return -1

    async def get_current_session(self) -> Optional[str]:
        """获取当前会话ID

        Returns:
            Optional[str]: 当前会话ID或None
        """
        return self.session_id

# 辅助函数：运行简单测试来快速验证服务


async def run_quick_test(host: str = "localhost", port: int = 50054) -> None:
    """运行快速测试来验证服务是否正常工作

    Args:
        host: 服务主机名
        port: 服务端口
    """
    client = SessionClient(host, port)

    try:
        await client.connect()

        # 测试Ping
        ping_result = await client.ping()
        print(f"Ping结果: {'成功' if ping_result else '失败'}")

        if ping_result:
            # 测试设置会话
            uid = 12345
            set_result = await client.set_session(uid)
            print(f"设置会话结果: 状态码={set_result[0]}, 会话ID={set_result[1]}")

            if set_result[0] == 0:
                session_id = set_result[1]

                # 测试获取会话
                get_result = await client.get_session(session_id)
                print(f"获取会话结果: 状态码={get_result[0]}, UID={get_result[1]}")

                # 测试删除会话
                del_result = await client.delete_session(session_id)
                print(f"删除会话结果: 状态码={del_result}")

                # 验证会话已删除
                get_after_del = await client.get_session(session_id)
                print(
                    f"删除后获取会话结果: 状态码={get_after_del[0]}, UID={get_after_del[1]}")

            # 测试服务重载
            reload_result = await client.reload_service()
            print(f"重新加载服务结果: 状态码={reload_result}")

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        await client.disconnect()

# 命令行直接运行时执行快速测试
if __name__ == "__main__":
    asyncio.run(run_quick_test())
