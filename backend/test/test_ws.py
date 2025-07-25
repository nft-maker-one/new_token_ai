import asyncio
import websockets
import datetime
import json
import uuid
import random

async def push_complete_task(websocket:websockets.WebSocketServerProtocol):
    while True:
        name = str(uuid.uuid4())
        inital_task = {
            'type':'new_token',
            'data':{
                'name':name[:8],
                'symbol':name[:3],
                'uri':'https://www.google.com',
                'mint':name[:5],
                'bonding_curve':name[:5],
                'user':name[:5],
                'creator':name[:5],
                'created_at':int(datetime.datetime.now().timestamp()),
                'virtual_token_reserves':1000000,
                'virtual_sol_reserves':100,
                'real_token_reserves':900000,
                'token_total_supply':1000000000

            }
        }
        await websocket.send(json.dumps(inital_task))
        await asyncio.sleep(2)
        analyze_task_msg = {
            "token_mint":name[:5],
            "token_symbol":name[:3],
            "token_name":name[:8],
            "status":"COMPLETED",
            "narrative_analysis":"test",
            "narrative_tag":"narrative",

            "risk_assessment":100,
            "market_analysis":"market_analysis",
            "market_tag":"market",
            "web_search_results":[{"title":name,"url":"https://www.google.com","snippet":name[:4],"relevance_score":random.randint(40,80)}],
            "tweet_result":[{"content":name,"link":"https://www.baidu.com"}],
            "ai_summary":"ai_summary",
            "ai_tag":"ai",
            "investment_recommendation":"investment_recommendation",
            "investment_tag":"investment",
            "analysis_completed_at":datetime.datetime.now().isoformat()
        }
      
        data = {'data':analyze_task_msg,'type':'analysis_complete'}
        await websocket.send(json.dumps(data))
        await asyncio.sleep(10)
        print("推送完成任务消息")


# 处理客户端连接的协程函数
async def handle_connection(websocket, path):
    try:
        print(f"新客户端连接: {websocket.remote_address}")
        connection_msg = {
            "type": "connection_status",
            "data": {"status": "connected"},
            "timestamp": datetime.datetime.now().isoformat()
        }
        connection_json = json.dumps(connection_msg)
        await websocket.send(connection_json)
        print("发送链接成功")
        asyncio.create_task(push_complete_task(websocket))
        # 持续接收客户端消息
        async for message in websocket: # 这个地方是异步操作
            print(f"收到消息: {message}")
            
            if message == "ping":
                await websocket.send("pong")
                print("回复消息pong")
            elif message == "heartbeat":
                heartbeat_response = json.dumps({
                        "type": "heartbeat_response",
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                await websocket.send(heartbeat_response)
                print("回复心跳信息")

            
    except websockets.exceptions.ConnectionClosedOK:
        print(f"客户端正常关闭连接: {websocket.remote_address}")
    except Exception as e:
        print(f"连接错误: {e}")
    finally:
        print(f"客户端断开连接: {websocket.remote_address}")

# 主函数：启动WebSocket服务器
async def main():
    # 绑定本地9999端口，使用handle_connection处理连接
    server = await websockets.serve(handle_connection, "localhost", 8000)
    
    print("WebSocket服务器已启动，监听地址: ws://localhost:9999")
    print("按Ctrl+C停止服务器...")
    
    # 保持服务器运行
    await server.wait_closed()

# 运行主函数
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已停止")    