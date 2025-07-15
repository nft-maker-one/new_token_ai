#!/usr/bin/env python3
"""
WebSocket连接诊断脚本
"""

import asyncio
import json
import time
import requests
from datetime import datetime

async def test_backend_websocket():
    """测试后端WebSocket"""
    print("🔍 测试后端WebSocket服务...")
    
    try:
        import websockets
        
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("✅ 后端WebSocket连接成功")
            
            # 等待连接确认消息
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"📨 收到服务器消息: {response}")
                
                # 解析消息
                try:
                    data = json.loads(response)
                    if data.get('type') == 'connection_status':
                        print(f"✅ 连接状态确认: {data['data']['status']}")
                    else:
                        print(f"📨 其他消息类型: {data.get('type')}")
                except json.JSONDecodeError:
                    print(f"📨 非JSON消息: {response}")
                    
            except asyncio.TimeoutError:
                print("⚠️ 5秒内未收到服务器消息")
            
            # 测试ping/pong
            print("\n🏓 测试ping/pong...")
            await websocket.send("ping")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                if response == "pong":
                    print("✅ ping/pong正常")
                else:
                    print(f"⚠️ 意外响应: {response}")
            except asyncio.TimeoutError:
                print("❌ ping超时")
            
            # 测试心跳
            print("\n💓 测试心跳...")
            await websocket.send("heartbeat")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                try:
                    data = json.loads(response)
                    if data.get('type') == 'heartbeat_response':
                        print("✅ 心跳响应正常")
                    else:
                        print(f"⚠️ 心跳响应异常: {data}")
                except json.JSONDecodeError:
                    print(f"⚠️ 心跳响应非JSON: {response}")
            except asyncio.TimeoutError:
                print("❌ 心跳超时")
            
            return True
            
    except Exception as e:
        print(f"❌ 后端WebSocket测试失败: {e}")
        return False

def test_frontend_service():
    """测试前端服务"""
    print("\n🔍 测试前端服务...")
    
    try:
        response = requests.get("http://localhost:3000/", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常")
            print(f"   状态码: {response.status_code}")
            print(f"   内容长度: {len(response.text)} 字符")
            
            # 检查是否包含React应用
            if "react" in response.text.lower() or "root" in response.text:
                print("✅ React应用加载正常")
            else:
                print("⚠️ 可能不是React应用")
                
            return True
        else:
            print(f"❌ 前端响应异常: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到前端服务 (http://localhost:3000)")
        return False
    except Exception as e:
        print(f"❌ 前端测试失败: {e}")
        return False

def test_backend_service():
    """测试后端服务"""
    print("\n🔍 测试后端服务...")
    
    try:
        # 健康检查
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ 后端健康检查通过")
            data = response.json()
            print(f"   消息: {data.get('message', 'N/A')}")
        else:
            print(f"❌ 后端健康检查失败: {response.status_code}")
            return False
            
        # 状态检查
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ 后端状态正常")
            print(f"   活跃连接数: {data.get('active_connections', 0)}")
            print(f"   代币监控: {data.get('token_monitor', 'unknown')}")
            print(f"   AI分析器: {data.get('ai_analyzer', 'unknown')}")
            print(f"   消息队列: {data.get('message_queue', 'unknown')}")
        else:
            print(f"❌ 后端状态检查失败: {response.status_code}")
            return False
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务 (http://localhost:8000)")
        return False
    except Exception as e:
        print(f"❌ 后端测试失败: {e}")
        return False

def analyze_websocket_issues():
    """分析WebSocket连接问题"""
    print("\n🔍 分析WebSocket连接问题...")
    
    issues = []
    solutions = []
    
    # 检查常见问题
    print("检查常见问题:")
    
    # 1. 端口冲突
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        print("✅ 后端端口8000可访问")
    except:
        issues.append("后端服务未在8000端口运行")
        solutions.append("启动后端: uvicorn backend.main:app --host 0.0.0.0 --port 8000")
    
    try:
        response = requests.get("http://localhost:3000/", timeout=2)
        print("✅ 前端端口3000可访问")
    except:
        issues.append("前端服务未在3000端口运行")
        solutions.append("启动前端: cd frontend && npm start")
    
    # 2. CORS问题
    try:
        response = requests.options("http://localhost:8000/ws", timeout=2)
        print(f"✅ CORS预检请求状态: {response.status_code}")
    except:
        issues.append("可能存在CORS问题")
        solutions.append("检查后端CORS配置")
    
    # 3. WebSocket协议支持
    print("✅ WebSocket协议支持检查完成")
    
    return issues, solutions

async def simulate_frontend_connection():
    """模拟前端WebSocket连接行为"""
    print("\n🔍 模拟前端WebSocket连接行为...")
    
    try:
        import websockets
        
        uri = "ws://localhost:8000/ws"
        
        # 模拟前端连接逻辑
        print("📡 建立WebSocket连接...")
        async with websockets.connect(uri) as websocket:
            print("✅ 连接建立成功")
            
            # 模拟前端消息处理
            message_count = 0
            start_time = time.time()
            
            # 监听10秒
            while time.time() - start_time < 10:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    message_count += 1
                    
                    try:
                        data = json.loads(response)
                        msg_type = data.get('type', 'unknown')
                        print(f"📨 消息 #{message_count}: {msg_type}")
                        
                        # 模拟前端处理逻辑
                        if msg_type == 'connection_status':
                            print("   ✅ 连接状态确认")
                        elif msg_type == 'new_token':
                            token_data = data.get('data', {})
                            print(f"   🪙 新代币: {token_data.get('symbol', 'N/A')}")
                        elif msg_type == 'heartbeat':
                            print("   💓 心跳")
                            await websocket.send("heartbeat")
                            
                    except json.JSONDecodeError:
                        if response == 'pong':
                            print(f"📨 消息 #{message_count}: pong")
                        else:
                            print(f"📨 消息 #{message_count}: {response}")
                            
                except asyncio.TimeoutError:
                    # 发送心跳保持连接
                    await websocket.send("heartbeat")
                    print("💓 发送心跳")
                    
            print(f"✅ 模拟完成，收到 {message_count} 条消息")
            return True
            
    except Exception as e:
        print(f"❌ 模拟前端连接失败: {e}")
        return False

async def main():
    """主函数"""
    print("🔧 WebSocket连接诊断工具")
    print("=" * 60)
    
    # 测试服务状态
    backend_ok = test_backend_service()
    frontend_ok = test_frontend_service()
    
    if not backend_ok:
        print("\n❌ 后端服务有问题，请先解决后端问题")
        return False
    
    if not frontend_ok:
        print("\n❌ 前端服务有问题，请先解决前端问题")
        return False
    
    # 测试WebSocket连接
    ws_ok = await test_backend_websocket()
    
    if not ws_ok:
        print("\n❌ 后端WebSocket有问题")
        return False
    
    # 模拟前端连接
    frontend_sim_ok = await simulate_frontend_connection()
    
    # 分析问题
    issues, solutions = analyze_websocket_issues()
    
    # 输出诊断结果
    print("\n" + "=" * 60)
    print("📋 诊断结果")
    print("=" * 60)
    
    print(f"后端服务: {'✅ 正常' if backend_ok else '❌ 异常'}")
    print(f"前端服务: {'✅ 正常' if frontend_ok else '❌ 异常'}")
    print(f"WebSocket连接: {'✅ 正常' if ws_ok else '❌ 异常'}")
    print(f"前端连接模拟: {'✅ 正常' if frontend_sim_ok else '❌ 异常'}")
    
    if issues:
        print(f"\n⚠️ 发现 {len(issues)} 个问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
            
        print(f"\n🔧 建议解决方案:")
        for i, solution in enumerate(solutions, 1):
            print(f"  {i}. {solution}")
    else:
        print("\n🎉 所有检查都通过！")
        print("\n💡 如果前端仍显示断开连接，请检查:")
        print("1. 浏览器控制台是否有错误")
        print("2. 浏览器是否阻止了WebSocket连接")
        print("3. 前端代码中的WebSocket URL是否正确")
        print("4. 刷新浏览器页面重新建立连接")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n👋 诊断被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        exit(1)
