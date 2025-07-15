import asyncio
import json
import base64
import struct
import websocket
import threading
import queue
from typing import Callable, Optional
import time
from datetime import datetime

from backend.models.token import CreateEvent, TokenData
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)

class TokenMonitor:
    """代币监控服务，基于原有的pump_pool_create.py逻辑"""

    def __init__(self, on_token_detected: Callable[[TokenData], None]):
        self.wss_url = "wss://mainnet.helius-rpc.com/?api-key=52eedaeb-aef0-4cc5-94a9-f4cdf8b9fb97"
        self.on_token_detected = on_token_detected
        self.ws: Optional[websocket.WebSocketApp] = None
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._min_create_event_size = 188
        self.main_loop = None  # 存储主事件循环的引用
        self.reconnect_attempts = 0  # 重连尝试次数
        self.max_reconnect_attempts = 10  # 最大重连次数
        self.count=0
        
    async def start_monitoring(self):
        """启动代币监控"""
        if self.is_running:
            logger.warning("代币监控已在运行中")
            return

        self.is_running = True
        # 保存主事件循环的引用
        self.main_loop = asyncio.get_event_loop()
        logger.info("启动代币监控服务...")

        # 在单独的线程中运行WebSocket
        self.monitor_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.monitor_thread.start()
        
    async def stop_monitoring(self):
        """停止代币监控"""
        self.is_running = False
        if self.ws:
            self.ws.close()
        logger.info("代币监控服务已停止")
        
    def _run_websocket(self):
        """在线程中运行WebSocket连接"""
        self.ws = websocket.WebSocketApp(
            self.wss_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )
        self.ws.run_forever()
        
    def _on_open(self, ws):
        """WebSocket连接打开时的回调"""
        # 重置重连计数
        
        self.reconnect_attempts = 0
        logger.info("WebSocket连接已建立")

        sub_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [
                {"mentions": ["6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"]},
                {"commitment": "processed"},
            ],
        }
        try:
            ws.send(json.dumps(sub_req))
            logger.info("已订阅代币创建事件...")
        except Exception as e:
            logger.error(f"发送订阅请求失败: {e}")
            
    def _on_message(self, ws, message):
        """处理WebSocket消息"""
        self.count+=1
        if self.count%5!=3:
            return

        try:
            payload = json.loads(message)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解码错误: {e}")
            return

        logs = payload.get("params", {}).get("result", {}).get("value", {}).get("logs", [])

        if any("Instruction: InitializeMint2" in log for log in logs):
            for entry in logs:
                # 跳过不是CreateEvent结构的日志
                if not entry.startswith("Program data: "):
                    continue
                if entry.startswith("Program data: vdt/"):
                    continue

                b64 = entry.split("Program data: ", 1)[1]
                try:
                    raw = base64.b64decode(b64)
                except Exception as e:
                    logger.error(f"Base64解码错误: {e}")
                    continue

                if len(raw) < self._min_create_event_size:
                    continue

                try:
                    event = self._parse_create_event(raw.hex())
                    if event:
                        # 转换为TokenData并异步处理
                        token_data = self._convert_to_token_data(event)
                        logger.info(f"🪙 准备调用回调函数处理代币: {token_data.symbol}")

                        # 使用保存的主事件循环来调用异步函数
                        if self.main_loop and not self.main_loop.is_closed():
                            try:
                                # 确保on_token_detected是异步函数
                                future = asyncio.run_coroutine_threadsafe(
                                    self.on_token_detected(token_data),
                                    self.main_loop
                                )
                                logger.info(f"🪙 异步任务已提交: {token_data.symbol}")
                            except Exception as e:
                                logger.error(f"❌ 提交异步任务失败: {e}")
                        else:
                            logger.error("❌ 主事件循环不可用，无法处理代币数据")
                        break
                except Exception as e:
                    logger.error(f"解析CreateEvent数据错误: {e}")
                    continue
   
    def _on_error(self, ws, error):
        """WebSocket错误回调"""
        logger.error(f"WebSocket错误: {error}")
        # 不要在错误回调中尝试重连，让close回调处理

    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭回调"""
        logger.info(f"WebSocket连接已关闭 (代码: {close_status_code}, 消息: {close_msg})")
        if self.is_running and self.reconnect_attempts < self.max_reconnect_attempts:
            # 如果应该继续运行且未超过重连次数，尝试重连
            self.reconnect_attempts += 1
            logger.info(f"尝试重新连接... ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            try:
                if self.main_loop and not self.main_loop.is_closed():
                    # 使用线程安全的方式调度重连
                    asyncio.run_coroutine_threadsafe(
                        self._reconnect(),
                        self.main_loop
                    )
                else:
                    # 如果没有主事件循环，使用线程定时器重连
                    import threading
                    timer = threading.Timer(5.0, self._sync_reconnect)
                    timer.start()
            except Exception as e:
                logger.error(f"重连调度失败: {e}")
                # 备用重连方法
                import threading
                timer = threading.Timer(5.0, self._sync_reconnect)
                timer.start()
        elif self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"已达到最大重连次数 ({self.max_reconnect_attempts})，停止重连")
            self.is_running = False
            
    async def _reconnect(self):
        """重新连接"""
        await asyncio.sleep(5)  # 等待5秒后重连
        if self.is_running:
            # 重新启动WebSocket连接
            self.monitor_thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.monitor_thread.start()

    def _sync_reconnect(self):
        """同步重连方法，用于线程环境"""
        if self.is_running:
            import time
            time.sleep(5)  # 等待5秒后重连
            if self.is_running:
                self.monitor_thread = threading.Thread(target=self._run_websocket, daemon=True)
                self.monitor_thread.start()
            
    def _parse_create_event(self, data_hex: str) -> CreateEvent:
        """解析创建事件数据（基于原有逻辑）"""
        data = bytes.fromhex(data_hex)
        offset = 8  # 跳过discriminator/padding

        def read_length_prefixed_string() -> str:
            nonlocal offset
            if offset + 4 > len(data):
                raise ValueError("字符串长度数据不足")
            (length,) = struct.unpack_from("<I", data, offset)
            offset += 4
            if length < 0 or offset + length > len(data):
                raise ValueError(f"无效的字符串长度 {length}")
            raw = data[offset : offset + length]
            offset += length
            return raw.decode("utf-8", errors="replace").rstrip("\x00")

        def read_pubkey_str() -> str:
            nonlocal offset
            if offset + 32 > len(data):
                raise ValueError("公钥数据不足")
            pk_bytes = data[offset : offset + 32]
            offset += 32
            from solders.pubkey import Pubkey
            return str(Pubkey.from_bytes(pk_bytes))

        # 解析字段
        name = read_length_prefixed_string()
        symbol = read_length_prefixed_string()
        uri = read_length_prefixed_string()
        mint = read_pubkey_str()
        bonding_curve = read_pubkey_str()
        user = read_pubkey_str()
        creator = read_pubkey_str()

        # 有符号64位时间戳
        if offset + 8 > len(data):
            raise ValueError("时间戳数据不足")
        (timestamp,) = struct.unpack_from("<q", data, offset)
        offset += 8

        # 无符号64位储备和供应量
        def read_u64() -> int:
            nonlocal offset
            if offset + 8 > len(data):
                raise ValueError("u64数据不足")
            (val,) = struct.unpack_from("<Q", data, offset)
            offset += 8
            return val

        virtual_token_reserves = read_u64()
        virtual_sol_reserves = read_u64()
        real_token_reserves = read_u64()
        token_total_supply = read_u64()

        return CreateEvent(
            name=name,
            symbol=symbol,
            uri=uri,
            mint=mint,
            bonding_curve=bonding_curve,
            user=user,
            creator=creator,
            timestamp=timestamp,
            virtual_token_reserves=virtual_token_reserves,
            virtual_sol_reserves=virtual_sol_reserves,
            real_token_reserves=real_token_reserves,
            token_total_supply=token_total_supply,
        )
        
    def _convert_to_token_data(self, event: CreateEvent) -> TokenData:
        """将CreateEvent转换为TokenData"""
        return TokenData(
            name=event.name,
            symbol=event.symbol,
            uri=event.uri,
            mint=event.mint,
            bonding_curve=event.bonding_curve,
            user=event.user,
            creator=event.creator,
            timestamp=event.timestamp,
            virtual_token_reserves=event.virtual_token_reserves/1e6,
            virtual_sol_reserves=event.virtual_sol_reserves/1e9,
            real_token_reserves=event.real_token_reserves/1e6,
            token_total_supply=event.token_total_supply/1e6,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
