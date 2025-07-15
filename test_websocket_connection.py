#!/usr/bin/env python3
"""
测试WebSocket连接的脚本
"""

import asyncio
import json
import time

async def test_websocket_connection():
    """测试WebSocket连接"""
    print("🔍 测试WebSocket连接...")
    
    try:
        import websockets
        
        uri = "ws://localhost:8000/ws"
        print(f"📡 连接到: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功建立")
            
            # 等待连接确认消息
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"📥 收到服务器消息: {response}")
                
                try:
                    data = json.loads(response)
                    if data.get('type') == 'connection_status':
                        print(f"✅ 连接状态确认: {data['data']['status']}")
                except json.JSONDecodeError:
                    print(f"📥 非JSON消息: {response}")
                    
            except asyncio.TimeoutError:
                print("⚠️ 未收到连接确认消息")
            
            print("\n📡 保持连接并监听消息...")
            start_time = time.time()
            message_count = 0
            
            # 保持连接60秒
            while time.time() - start_time < 60:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    message_count += 1
                    print(f"📥 消息 #{message_count}: {response[:100]}{'...' if len(response) > 100 else ''}")
                    
                    # 如果是心跳，回应
                    try:
                        data = json.loads(response)
                        if data.get('type') == 'heartbeat':
                            await websocket.send("heartbeat")
                            print("💓 回应心跳")
                    except:
                        pass
                        
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    await websocket.send("heartbeat")
                    print("💓 发送心跳")
                    
            print(f"\n✅ 测试完成，共收到 {message_count} 条消息")
            return True
            
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")
        return False

async def main():
    """主函数"""
    print("🧪 WebSocket连接测试")
    print("=" * 50)
    
    result = await test_websocket_connection()
    
    print("\n" + "=" * 50)
    if result:
        print("🎉 WebSocket连接测试成功！")
    else:
        print("❌ WebSocket连接测试失败！")
    
    return result

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        exit(1)
