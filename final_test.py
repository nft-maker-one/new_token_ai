#!/usr/bin/env python3
"""
最终系统测试脚本
"""

import requests
import time
import json

def test_backend():
    """测试后端服务"""
    print("🔍 测试后端服务...")
    
    try:
        # 测试健康检查
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ 后端健康检查通过")
            data = response.json()
            print(f"   响应: {data}")
        else:
            print(f"❌ 后端健康检查失败: {response.status_code}")
            return False
            
        # 测试状态端点
        response = requests.get("http://localhost:8000/status", timeout=5)
        if response.status_code == 200:
            print("✅ 后端状态端点正常")
            data = response.json()
            print(f"   活跃连接数: {data.get('active_connections', 0)}")
            print(f"   代币监控: {data.get('token_monitor', 'unknown')}")
            print(f"   AI分析器: {data.get('ai_analyzer', 'unknown')}")
        else:
            print(f"❌ 后端状态端点失败: {response.status_code}")
            return False
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务 (http://localhost:8000)")
        return False
    except Exception as e:
        print(f"❌ 后端测试失败: {e}")
        return False

def test_frontend():
    """测试前端服务"""
    print("\n🔍 测试前端服务...")
    
    try:
        response = requests.get("http://localhost:3000/", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常")
            print("   前端可以在浏览器中访问")
        else:
            print(f"❌ 前端响应异常: {response.status_code}")
            return False
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到前端服务 (http://localhost:3000)")
        return False
    except Exception as e:
        print(f"❌ 前端测试失败: {e}")
        return False

def test_websocket():
    """测试WebSocket连接"""
    print("\n🔍 测试WebSocket连接...")
    
    try:
        import websockets
        import asyncio
        
        async def test_ws():
            try:
                uri = "ws://localhost:8000/ws"
                async with websockets.connect(uri) as websocket:
                    print("✅ WebSocket连接成功")
                    
                    # 发送ping消息
                    await websocket.send("ping")
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    
                    if response == "pong":
                        print("✅ WebSocket通信正常")
                        return True
                    else:
                        print(f"⚠️ 意外的响应: {response}")
                        return False
                        
            except Exception as e:
                print(f"❌ WebSocket测试失败: {e}")
                return False
        
        return asyncio.run(test_ws())
        
    except ImportError:
        print("⚠️ websockets库未安装，跳过WebSocket测试")
        return True
    except Exception as e:
        print(f"❌ WebSocket测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 AI Crypto Token Analysis 最终系统测试")
    print("=" * 60)
    
    tests = [
        ("后端服务", test_backend),
        ("前端服务", test_frontend),
        ("WebSocket连接", test_websocket),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
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
        print("\n🎉 所有测试通过！系统运行正常。")
        print("\n📖 使用说明:")
        print("1. 前端界面: http://localhost:3000")
        print("2. 后端API: http://localhost:8000")
        print("3. API文档: http://localhost:8000/docs")
        print("4. 运行演示: python demo_tokens.py")
        return True
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        
        if not results[0][1]:  # 后端失败
            print("\n🔧 后端启动方法:")
            print("   venv\\Scripts\\python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000")
        
        if not results[1][1]:  # 前端失败
            print("\n🔧 前端启动方法:")
            print("   cd frontend && npm start")
        
        return False

if __name__ == "__main__":
    try:
        result = main()
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
        exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        exit(1)
