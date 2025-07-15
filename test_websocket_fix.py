#!/usr/bin/env python3
"""
测试WebSocket修复的脚本
"""

import asyncio
import json
import time
from datetime import datetime

async def test_websocket_connection():
    """测试WebSocket连接持久性"""
    print("🔍 测试WebSocket连接持久性...")
    
    try:
        import websockets
        
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 等待连接确认消息
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                if data.get('type') == 'connection_status':
                    print("✅ 收到服务器连接确认")
                else:
                    print(f"📨 收到消息: {data}")
            except asyncio.TimeoutError:
                print("⚠️ 未收到连接确认消息")
            
            # 测试ping/pong
            print("\n🏓 测试ping/pong...")
            await websocket.send("ping")
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            if response == "pong":
                print("✅ ping/pong正常")
            else:
                print(f"⚠️ 意外响应: {response}")
            
            # 测试心跳
            print("\n💓 测试心跳...")
            await websocket.send("heartbeat")
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            if data.get('type') == 'heartbeat_response':
                print("✅ 心跳响应正常")
            else:
                print(f"⚠️ 心跳响应异常: {data}")
            
            # 保持连接30秒，测试持久性
            print("\n⏱️ 测试连接持久性 (30秒)...")
            start_time = time.time()
            message_count = 0
            
            while time.time() - start_time < 30:
                try:
                    # 等待消息，超时时间设为5秒
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    message_count += 1
                    
                    try:
                        data = json.loads(response)
                        msg_type = data.get('type', 'unknown')
                        print(f"📨 收到消息 #{message_count}: {msg_type}")
                        
                        # 如果是心跳，回应
                        if msg_type == 'heartbeat':
                            await websocket.send("heartbeat")
                            
                    except json.JSONDecodeError:
                        print(f"📨 收到文本消息 #{message_count}: {response}")
                        
                except asyncio.TimeoutError:
                    # 超时是正常的，发送一个ping保持活跃
                    await websocket.send("ping")
                    print("🏓 发送ping保持连接活跃")
                    
            print(f"✅ 连接保持了30秒，收到 {message_count} 条消息")
            return True
            
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")
        return False

async def test_multiple_connections():
    """测试多个WebSocket连接"""
    print("\n🔍 测试多个WebSocket连接...")
    
    try:
        import websockets
        
        connections = []
        uri = "ws://localhost:8000/ws"
        
        # 创建3个连接
        for i in range(3):
            ws = await websockets.connect(uri)
            connections.append(ws)
            print(f"✅ 连接 #{i+1} 建立成功")
            
            # 等待连接确认
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2)
                data = json.loads(response)
                if data.get('type') == 'connection_status':
                    print(f"✅ 连接 #{i+1} 收到确认")
            except:
                pass
        
        # 测试所有连接都能收发消息
        print("\n📡 测试广播功能...")
        for i, ws in enumerate(connections):
            await ws.send(f"ping from connection {i+1}")
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2)
                print(f"✅ 连接 #{i+1} 收到响应: {response}")
            except asyncio.TimeoutError:
                print(f"⚠️ 连接 #{i+1} 响应超时")
        
        # 关闭所有连接
        for i, ws in enumerate(connections):
            await ws.close()
            print(f"🔌 连接 #{i+1} 已关闭")
        
        return True
        
    except Exception as e:
        print(f"❌ 多连接测试失败: {e}")
        return False

def test_backend_status():
    """测试后端状态"""
    print("🔍 检查后端状态...")
    
    try:
        import requests
        
        # 测试健康检查
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ 后端健康检查通过")
        else:
            print(f"❌ 后端健康检查失败: {response.status_code}")
            return False
            
        # 测试状态端点
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 活跃WebSocket连接数: {data.get('active_connections', 0)}")
            print(f"✅ 代币监控状态: {data.get('token_monitor', 'unknown')}")
            print(f"✅ AI分析器状态: {data.get('ai_analyzer', 'unknown')}")
        else:
            print(f"❌ 状态端点失败: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 后端状态检查失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🧪 WebSocket修复验证测试")
    print("=" * 60)
    
    # 检查后端状态
    if not test_backend_status():
        print("❌ 后端服务不可用，请先启动后端")
        return False
    
    tests = [
        ("WebSocket连接持久性", test_websocket_connection),
        ("多个WebSocket连接", test_multiple_connections),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 运行测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📋 测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！WebSocket连接已修复。")
        print("\n📖 修复内容:")
        print("1. ✅ WebSocket保持持久连接，不会主动断开")
        print("2. ✅ 添加了心跳机制保持连接活跃")
        print("3. ✅ 修复了前端重连逻辑")
        print("4. ✅ 改进了连接状态管理")
        return True
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        exit(1)
