#!/usr/bin/env python3
"""
系统测试脚本
"""

import asyncio
import json
import websockets
from datetime import datetime
from backend.models.token import TokenData

async def test_websocket_connection():
    """测试WebSocket连接"""
    print("🔗 测试WebSocket连接...")
    
    try:
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket连接成功")
            
            # 发送ping消息
            await websocket.send("ping")
            response = await websocket.recv()
            
            if response == "pong":
                print("✓ WebSocket通信正常")
                return True
            else:
                print(f"✗ 意外的响应: {response}")
                return False
                
    except Exception as e:
        print(f"✗ WebSocket连接失败: {e}")
        return False

async def test_token_data_model():
    """测试代币数据模型"""
    print("\n📊 测试数据模型...")
    
    try:
        # 创建测试代币数据
        token_data = TokenData(
            name="Test Token",
            symbol="TEST",
            uri="https://example.com/metadata.json",
            mint="11111111111111111111111111111111",
            bonding_curve="22222222222222222222222222222222",
            user="33333333333333333333333333333333",
            creator="44444444444444444444444444444444",
            timestamp=int(datetime.now().timestamp()),
            virtual_token_reserves=1000000,
            virtual_sol_reserves=100,
            real_token_reserves=900000,
            token_total_supply=1000000000
        )
        
        # 测试序列化
        json_data = token_data.json()
        parsed_data = TokenData.parse_raw(json_data)
        
        print("✓ 数据模型测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 数据模型测试失败: {e}")
        return False

async def simulate_token_analysis():
    """模拟代币分析流程"""
    print("\n🤖 模拟代币分析流程...")
    
    try:
        from backend.services.message_queue import MessageQueue
        from backend.services.ai_analyzer import AIAnalyzer
        
        # 初始化服务
        message_queue = MessageQueue()
        await message_queue.initialize()
        
        # 注意：这里需要设置GEMINI_API_KEY环境变量
        import os
        if not os.getenv("GEMINI_API_KEY"):
            print("⚠ GEMINI_API_KEY未设置，跳过AI分析测试")
            return True
            
        ai_analyzer = AIAnalyzer(message_queue)
        await ai_analyzer.initialize()
        
        # 创建测试代币
        test_token = TokenData(
            name="Test Meme Token",
            symbol="MEME",
            uri="https://example.com/meme.json",
            mint="55555555555555555555555555555555",
            bonding_curve="66666666666666666666666666666666",
            user="77777777777777777777777777777777",
            creator="88888888888888888888888888888888",
            timestamp=int(datetime.now().timestamp()),
            virtual_token_reserves=1000000,
            virtual_sol_reserves=100,
            real_token_reserves=900000,
            token_total_supply=1000000000
        )
        
        # 添加到分析队列
        await message_queue.add_analysis_task(test_token)
        
        # 检查队列大小
        queue_size = await message_queue.get_queue_size()
        if queue_size > 0:
            print("✓ 代币已成功添加到分析队列")
        else:
            print("✗ 代币添加到队列失败")
            return False
            
        # 清理
        await message_queue.close()
        
        print("✓ 代币分析流程测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 代币分析流程测试失败: {e}")
        return False

async def test_api_endpoints():
    """测试API端点"""
    print("\n🌐 测试API端点...")
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # 测试健康检查
            async with session.get('http://localhost:8000/') as response:
                if response.status == 200:
                    data = await response.json()
                    print("✓ 健康检查端点正常")
                else:
                    print(f"✗ 健康检查失败: {response.status}")
                    return False
            
            # 测试状态端点
            async with session.get('http://localhost:8000/status') as response:
                if response.status == 200:
                    data = await response.json()
                    print("✓ 状态端点正常")
                    print(f"  - 活跃连接数: {data.get('active_connections', 0)}")
                else:
                    print(f"✗ 状态端点失败: {response.status}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"✗ API端点测试失败: {e}")
        return False

def test_frontend_files():
    """测试前端文件"""
    print("\n📱 检查前端文件...")
    
    import os
    from pathlib import Path
    
    frontend_dir = Path("frontend")
    required_files = [
        "package.json",
        "src/App.js",
        "src/index.js",
        "src/components/TokenCard.js",
        "src/components/StatusBar.js",
        "src/hooks/useWebSocket.js"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = frontend_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"✗ 缺少前端文件: {missing_files}")
        return False
    else:
        print("✓ 所有前端文件存在")
        return True

async def main():
    """主测试函数"""
    print("🧪 AI Crypto Token Analysis 系统测试")
    print("=" * 50)
    
    tests = [
        ("前端文件检查", test_frontend_files),
        ("数据模型测试", test_token_data_model),
        ("API端点测试", test_api_endpoints),
        ("WebSocket连接测试", test_websocket_connection),
        ("代币分析流程测试", simulate_token_analysis),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 运行测试: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📋 测试结果汇总:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统准备就绪。")
        return True
    else:
        print("⚠ 部分测试失败，请检查配置和依赖。")
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
