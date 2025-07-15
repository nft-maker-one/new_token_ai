#!/usr/bin/env python3
"""
演示代币生成器 - 用于测试系统功能
"""

import asyncio
import json
import random
import time
from datetime import datetime
import websockets
from backend.models.token import TokenData

# 演示代币数据
DEMO_TOKENS = [
    {
        "name": "Doge Killer",
        "symbol": "DOGEK",
        "category": "MEME",
        "description": "The next generation meme token to surpass Dogecoin"
    },
    {
        "name": "AI Trading Bot",
        "symbol": "AIBOT",
        "category": "AI",
        "description": "Revolutionary AI-powered trading automation platform"
    },
    {
        "name": "Meta Gaming",
        "symbol": "MGAME",
        "category": "GAMING",
        "description": "Metaverse gaming platform with NFT integration"
    },
    {
        "name": "Green Energy",
        "symbol": "GREEN",
        "category": "DEFI",
        "description": "Sustainable DeFi protocol for renewable energy projects"
    },
    {
        "name": "Pepe 2.0",
        "symbol": "PEPE2",
        "category": "MEME",
        "description": "The evolution of the legendary Pepe meme token"
    }
]

def generate_random_address():
    """生成随机地址"""
    import secrets
    return ''.join(secrets.choice('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz') for _ in range(44))

def create_demo_token(token_info):
    """创建演示代币数据"""
    return TokenData(
        name=token_info["name"],
        symbol=token_info["symbol"],
        uri=f"https://example.com/{token_info['symbol'].lower()}.json",
        mint=generate_random_address(),
        bonding_curve=generate_random_address(),
        user=generate_random_address(),
        creator=generate_random_address(),
        timestamp=int(datetime.now().timestamp()),
        virtual_token_reserves=random.randint(500000, 2000000),
        virtual_sol_reserves=random.randint(50, 500),
        real_token_reserves=random.randint(400000, 1800000),
        token_total_supply=random.randint(100000000, 1000000000),
        created_at=datetime.now()
    )

async def send_demo_tokens():
    """发送演示代币到后端"""
    print("🎭 启动演示代币生成器...")
    print("连接到后端服务...")
    
    try:
        # 这里我们直接调用后端函数，而不是通过WebSocket
        from backend.main import handle_new_token
        
        for i, token_info in enumerate(DEMO_TOKENS):
            print(f"\n📤 发送演示代币 {i+1}/{len(DEMO_TOKENS)}: {token_info['name']}")
            
            # 创建代币数据
            token_data = create_demo_token(token_info)
            
            # 发送到后端处理
            await handle_new_token(token_data)
            
            print(f"✓ 代币 {token_info['symbol']} 已发送")
            
            # 等待一段时间再发送下一个
            await asyncio.sleep(random.randint(5, 15))
        
        print("\n🎉 所有演示代币已发送完毕！")
        print("请查看前端界面观察AI分析进度")
        
    except Exception as e:
        print(f"❌ 发送演示代币失败: {e}")

async def continuous_demo():
    """持续发送演示代币"""
    print("🔄 启动持续演示模式...")
    print("每30-60秒发送一个随机代币")
    print("按Ctrl+C停止")
    
    try:
        from backend.main import handle_new_token
        
        while True:
            # 随机选择一个代币模板
            token_info = random.choice(DEMO_TOKENS)
            
            # 稍微修改名称以避免重复
            token_info = token_info.copy()
            token_info["name"] += f" #{random.randint(1000, 9999)}"
            token_info["symbol"] += str(random.randint(10, 99))
            
            print(f"\n📤 发送代币: {token_info['name']}")
            
            # 创建并发送代币
            token_data = create_demo_token(token_info)
            await handle_new_token(token_data)
            
            print(f"✓ 代币 {token_info['symbol']} 已发送")
            
            # 等待30-60秒
            wait_time = random.randint(30, 60)
            print(f"⏳ 等待 {wait_time} 秒...")
            await asyncio.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("\n👋 演示已停止")
    except Exception as e:
        print(f"❌ 持续演示失败: {e}")

async def test_websocket_demo():
    """通过WebSocket发送演示数据"""
    print("🔌 通过WebSocket发送演示数据...")
    
    try:
        uri = "ws://localhost:8000/ws"
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket连接成功")
            
            for token_info in DEMO_TOKENS:
                token_data = create_demo_token(token_info)
                
                message = {
                    "type": "new_token",
                    "data": token_data.dict(),
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(message))
                print(f"📤 发送: {token_info['name']}")
                
                await asyncio.sleep(5)
                
    except Exception as e:
        print(f"❌ WebSocket演示失败: {e}")

def main():
    """主函数"""
    print("🎭 AI Crypto Token Analysis 演示工具")
    print("=" * 50)
    
    print("选择演示模式:")
    print("1. 发送一批演示代币")
    print("2. 持续发送演示代币")
    print("3. WebSocket演示")
    print("4. 退出")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        print("\n🚀 启动批量演示...")
        asyncio.run(send_demo_tokens())
    elif choice == "2":
        print("\n🔄 启动持续演示...")
        asyncio.run(continuous_demo())
    elif choice == "3":
        print("\n🔌 启动WebSocket演示...")
        asyncio.run(test_websocket_demo())
    elif choice == "4":
        print("👋 再见！")
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
