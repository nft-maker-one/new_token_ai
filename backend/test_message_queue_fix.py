#!/usr/bin/env python3
"""
测试消息队列修复
验证任务队列和结果队列是否正确分离
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from backend.models.token import TokenData, AnalysisResult
from backend.services.message_queue import MessageQueue

async def test_message_queue_separation():
    """测试消息队列的任务和结果分离"""
    print("🧪 测试消息队列修复...")
    
    # 初始化消息队列
    message_queue = MessageQueue()
    await message_queue.initialize()
    
    # 创建测试代币数据
    token_data = TokenData(
        name="Test Token",
        symbol="TEST",
        uri="https://example.com",
        mint="DztwRrFQF4tbJLxQo9EQ7fk36xQkvoiYwxBLBQW3pump",
        bonding_curve="bonding_curve_address",
        user="user_address",
        creator="creator_address",
        timestamp=1642723200,
        virtual_token_reserves=1000000,
        virtual_sol_reserves=500,
        real_token_reserves=800000,
        token_total_supply=1000000000,
        created_at=datetime.now()
    )
    
    # 创建测试分析结果
    analysis_result = AnalysisResult(
        token_mint="DztwRrFQF4tbJLxQo9EQ7fk36xQkvoiYwxBLBQW3pump",
        token_symbol="TEST",
        token_name="Test Token",
        status="COMPLETED",
        progress=100.0,
        narrative_analysis="Test narrative",
        risk_assessment="Test risk",
        market_analysis="Test market",
        ai_summary="Test summary",
        investment_recommendation="Test recommendation",
        analysis_started_at=datetime.now(),
        analysis_completed_at=datetime.now()
    )
    
    print("✅ 测试数据创建成功")
    
    # 测试1: 添加分析任务
    print("\n🔍 测试1: 添加分析任务到任务队列")
    await message_queue.add_analysis_task(token_data)
    print("✅ 任务添加成功")
    
    # 测试2: 从任务队列获取任务
    print("\n🔍 测试2: 从任务队列获取任务")
    task = await message_queue.get_analysis_task()
    if task and "token_data" in task:
        print(f"✅ 任务获取成功: {task['task_id']}")
        print(f"   包含token_data: {task['token_data']['symbol']}")
    else:
        print(f"❌ 任务获取失败或格式错误: {task}")
        return False
    
    # 测试3: 发布分析结果
    print("\n🔍 测试3: 发布分析结果到结果队列")
    await message_queue.publish_analysis_result(analysis_result)
    print("✅ 结果发布成功")
    
    # 测试4: 从结果队列获取结果
    print("\n🔍 测试4: 从结果队列获取结果")
    result_message = await message_queue.get_result_message()
    if result_message:
        try:
            result_data = json.loads(result_message)
            if result_data.get("type") == "analysis_complete":
                print(f"✅ 结果获取成功: {result_data['type']}")
                print(f"   代币符号: {result_data['data']['token_symbol']}")
            else:
                print(f"❌ 结果格式错误: {result_data}")
                return False
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            return False
    else:
        print("❌ 结果获取失败")
        return False
    
    # 测试5: 验证队列分离
    print("\n🔍 测试5: 验证队列分离")
    
    # 添加更多任务和结果
    await message_queue.add_analysis_task(token_data)
    await message_queue.publish_analysis_result(analysis_result)
    
    # 检查任务队列
    task_queue_size = await message_queue.get_queue_size()
    print(f"   任务队列大小: {task_queue_size}")
    
    # 获取任务应该得到任务格式
    task2 = await message_queue.get_analysis_task()
    if task2 and "token_data" in task2:
        print("✅ 任务队列正确返回任务格式")
    else:
        print("❌ 任务队列返回格式错误")
        return False
    
    # 获取结果应该得到结果格式
    result2 = await message_queue.get_result_message()
    if result2:
        try:
            result_data2 = json.loads(result2)
            if result_data2.get("type") == "analysis_complete":
                print("✅ 结果队列正确返回结果格式")
            else:
                print("❌ 结果队列返回格式错误")
                return False
        except:
            print("❌ 结果队列返回无效JSON")
            return False
    else:
        print("❌ 结果队列无数据")
        return False
    
    print("\n🎉 所有测试通过！消息队列修复成功")
    return True

async def test_ai_analyzer_compatibility():
    """测试AI分析器兼容性"""
    print("\n🧪 测试AI分析器兼容性...")
    
    # 模拟AI分析器处理任务的场景
    message_queue = MessageQueue()
    await message_queue.initialize()
    
    # 创建测试任务
    token_data = TokenData(
        name="Test Token",
        symbol="TEST",
        uri="https://example.com",
        mint="DztwRrFQF4tbJLxQo9EQ7fk36xQkvoiYwxBLBQW3pump",
        bonding_curve="bonding_curve_address",
        user="user_address",
        creator="creator_address",
        timestamp=1642723200,
        virtual_token_reserves=1000000,
        virtual_sol_reserves=500,
        real_token_reserves=800000,
        token_total_supply=1000000000,
        created_at=datetime.now()
    )
    
    # 添加任务
    await message_queue.add_analysis_task(token_data)
    
    # 模拟AI分析器获取任务
    task = await message_queue.get_analysis_task()
    
    try:
        # 这是AI分析器中会执行的代码
        token_data_dict = task["token_data"]
        reconstructed_token = TokenData(**token_data_dict)
        
        print(f"✅ AI分析器兼容性测试通过")
        print(f"   重构的代币: {reconstructed_token.symbol}")
        return True
        
    except KeyError as e:
        print(f"❌ AI分析器兼容性测试失败: 缺少键 {e}")
        return False
    except Exception as e:
        print(f"❌ AI分析器兼容性测试失败: {e}")
        return False

async def main():
    """运行所有测试"""
    print("🚀 开始消息队列修复验证测试")
    print("=" * 50)
    
    tests = [
        test_message_queue_separation,
        test_ai_analyzer_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！消息队列修复成功")
        return 0
    else:
        print("❌ 部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
