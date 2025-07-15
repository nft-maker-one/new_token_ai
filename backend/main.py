import asyncio
import json
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from backend.services.token_monitor import TokenMonitor
from backend.services.ai_analyzer import AIAnalyzer
from backend.services.message_queue import MessageQueue
from backend.models.token import TokenData, AnalysisResult
from backend.utils.logger import setup_logger
from backend.utils.env_loader import get_env_var

# 设置日志
logger = setup_logger(__name__)

app = FastAPI(title="AI Crypto Token Analysis API", version="1.0.0")

# CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局服务实例
token_monitor: Optional[TokenMonitor] = None
ai_analyzer: Optional[AIAnalyzer] = None
message_queue: Optional[MessageQueue] = None

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket连接已建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket连接已断开，当前连接数: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"发送个人消息失败: {e}")
            # 只有在连接真正断开时才移除，不要主动断开
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        if not self.active_connections:
            logger.warning("⚠️ 没有活跃的WebSocket连接，跳过广播")
            return

        logger.info(f"📡 开始广播消息到 {len(self.active_connections)} 个连接")
        logger.info(f"📡 广播内容: {message[:200]}{'...' if len(message) > 200 else ''}")

        disconnected = []
        success_count = 0

        for i, connection in enumerate(self.active_connections):
            try:
                await connection.send_text(message)
                success_count += 1
                logger.info(f"✅ 成功发送到连接 #{i+1}")
            except Exception as e:
                logger.error(f"❌ 发送到连接 #{i+1} 失败: {e}")
                # 标记为断开，但不主动关闭连接
                disconnected.append(connection)

        # 只清理真正断开的连接，不主动断开
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

        logger.info(f"📡 广播完成: 成功 {success_count}/{len(self.active_connections) + len(disconnected)} 个连接")

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global token_monitor, ai_analyzer, message_queue
    
    logger.info("正在启动AI Crypto Token Analysis服务...")
    
    # 初始化消息队列
    message_queue = MessageQueue()
    await message_queue.initialize()
    
    # 初始化AI分析器 - 设置最大并发AI请求数
    max_concurrent_ai_requests = int(get_env_var("MAX_CONCURRENT_AI_REQUESTS", "3"))
    ai_analyzer = AIAnalyzer(message_queue, max_concurrent_ai_requests)
    await ai_analyzer.initialize()
    
    # 初始化代币监控器
    token_monitor = TokenMonitor(on_token_detected=handle_new_token)
    
    # 启动AI分析器的消费者
    asyncio.create_task(ai_analyzer.start_consumer())

    # 启动代币监控
    asyncio.create_task(token_monitor.start_monitoring())

    # 启动分析结果广播任务
    asyncio.create_task(broadcast_analysis_results())
    
    logger.info("所有服务已成功启动")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    logger.info("正在关闭服务...")
    
    if token_monitor:
        await token_monitor.stop_monitoring()
    
    if ai_analyzer:
        await ai_analyzer.stop()
    
    if message_queue:
        await message_queue.close()
    
    logger.info("所有服务已关闭")

async def handle_new_token(token_data: TokenData):
    """处理新检测到的代币"""
    logger.info(f"🪙 [START] handle_new_token 开始处理: {token_data.symbol}")

    try:
        logger.info(f"🪙 检测到新代币: {token_data.symbol} ({token_data.name})")
        logger.info(f"🪙 代币详情: mint={token_data.mint}, 总供应量={token_data.token_total_supply}")

        # 立即向前端推送代币信息
        logger.info(f"📤 [STEP 1] 准备创建代币消息: {token_data.symbol}")
        token_message = {
            "type": "new_token",
            "data": token_data.to_json_dict(),  # 使用安全的JSON序列化方法
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"📤 [STEP 2] 序列化消息: {token_data.symbol}")
        token_json = json.dumps(token_message)
        logger.info(f"📤 [STEP 3] 准备广播新代币消息: {token_data.symbol}")
        logger.info(f"📤 消息内容: {token_json[:300]}{'...' if len(token_json) > 300 else ''}")

        logger.info(f"📤 [STEP 4] 调用manager.broadcast: {token_data.symbol}")
        try:
            await manager.broadcast(token_json)
            logger.info(f"📤 [STEP 5] 广播完成: {token_data.symbol}")
        except Exception as e:
            logger.error(f"❌ 广播失败: {e}")
            logger.error(f"❌ 广播失败的代币: {token_data.symbol}")
            import traceback
            logger.error(f"❌ 错误详情: {traceback.format_exc()}")

        # 将代币添加到分析队列
        logger.info(f"📝 [STEP 6] 准备添加到分析队列: {token_data.symbol}")
        if message_queue:
            logger.info(f"📝 将代币 {token_data.symbol} 添加到分析队列")
            await message_queue.add_analysis_task(token_data)
        else:
            logger.warning("⚠️ 消息队列不可用，跳过分析任务")

        # logger.info(f"🪙 [END] handle_new_token 处理完成: {token_data.symbol}")

    except Exception as e:
        logger.error(f"❌ handle_new_token 处理失败: {token_data.symbol}")
        logger.error(f"❌ 错误: {e}")
        import traceback
        logger.error(f"❌ 完整错误: {traceback.format_exc()}")

async def broadcast_analysis_results():
    """广播分析结果"""
    if not message_queue or not message_queue.redis_client:
        return

    try:
        if message_queue.redis_client:
            pubsub = message_queue.redis_client.pubsub()
            await pubsub.subscribe(message_queue.result_channel)   
            logger.info("开始监听分析结果...")

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # 广播分析结果到所有WebSocket连接
                        await manager.broadcast(message['data'])
                        logger.info(f"广播分析结果成功: {message['data']}")
                    except Exception as e:
                        logger.error(f"广播分析结果失败: {e}")
        else:
            # 从内存队列获取消息
            while True:
                message = await message_queue._memory_queue.get()
                try:
                    # 广播分析结果到所有WebSocket连接
                    # 这个地方需要广播整个 message
                    # type data timestamp
                    await manager.broadcast(message)
                except Exception as e:
                    logger.error(f"广播分析结果失败: {e}")

    except Exception as e:
        logger.error(f"分析结果广播任务失败: {e}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，用于实时通信"""
    client_ip = websocket.client.host if websocket.client else "unknown"
    logger.info(f"🔗 新的WebSocket连接请求来自: {client_ip}")

    await manager.connect(websocket)
    try:
        # 发送连接成功消息
        connection_msg = {
            "type": "connection_status",
            "data": {"status": "connected"},
            "timestamp": datetime.now().isoformat()
        }
        connection_json = json.dumps(connection_msg)
        await websocket.send_text(connection_json)
        logger.info(f"📤 发送连接确认消息到 {client_ip}: {connection_json}")

        while True:
            # 保持连接活跃，设置较长的超时时间
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                logger.info(f"📥 收到来自 {client_ip} 的消息: {data}")

                # 处理客户端发送的消息
                if data == "ping":
                    await websocket.send_text("pong")
                    logger.info(f"📤 发送pong响应到 {client_ip}")
                elif data == "heartbeat":
                    heartbeat_response = json.dumps({
                        "type": "heartbeat_response",
                        "timestamp": datetime.now().isoformat()
                    })
                    await websocket.send_text(heartbeat_response)
                    logger.info(f"📤 发送心跳响应到 {client_ip}: {heartbeat_response}")
                else:
                    logger.warning(f"⚠️ 收到未知消息类型从 {client_ip}: {data}")

            except asyncio.TimeoutError:
                # 发送心跳检查连接是否还活跃
                try:
                    heartbeat_msg = json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })
                    await websocket.send_text(heartbeat_msg)
                    logger.info(f"💓 发送心跳到 {client_ip}: {heartbeat_msg}")
                except Exception as e:
                    logger.error(f"❌ 发送心跳失败到 {client_ip}: {e}")
                    break
            except WebSocketDisconnect:
                logger.info(f"🔌 客户端 {client_ip} 主动断开WebSocket连接")
                break
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket连接断开: {client_ip}")
    except Exception as e:
        logger.error(f"❌ WebSocket错误 ({client_ip}): {e}")
    finally:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "message": "AI Crypto Token Analysis API",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def get_status():
    """获取系统状态"""
    return {
        "token_monitor": "running" if token_monitor else "stopped",
        "ai_analyzer": "running" if ai_analyzer else "stopped",
        "message_queue": "running" if message_queue else "stopped",
        "active_connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
