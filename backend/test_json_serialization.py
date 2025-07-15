#!/usr/bin/env python3
"""
测试JSON序列化修复
验证datetime对象能否正确序列化
"""

import json
import sys
import os
from datetime import datetime

# 添加backend目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.token import TokenData, AnalysisResult, NarrativeAnalysis, RiskLevel, MarketAnalysis

def test_token_data_serialization():
    """测试TokenData的JSON序列化"""
    print("🧪 测试TokenData序列化...")
    
    # 创建测试数据
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
    
    try:
        # 测试旧方法（应该失败）
        try:
            old_dict = token_data.model_dump()
            json.dumps(old_dict)
            print("❌ 旧方法意外成功了")
        except TypeError as e:
            print(f"✅ 旧方法正确失败: {e}")
        
        # 测试新方法（应该成功）
        new_dict = token_data.to_json_dict()
        json_str = json.dumps(new_dict)
        print(f"✅ 新方法成功: JSON长度 {len(json_str)} 字符")
        
        # 验证反序列化
        parsed = json.loads(json_str)
        print(f"✅ 反序列化成功: created_at = {parsed['created_at']}")
        
        return True
        
    except Exception as e:
        print(f"❌ TokenData序列化测试失败: {e}")
        return False

def test_analysis_result_serialization():
    """测试AnalysisResult的JSON序列化"""
    print("\n🧪 测试AnalysisResult序列化...")
    
    # 创建测试数据
    analysis_result = AnalysisResult(
        token_mint="DztwRrFQF4tbJLxQo9EQ7fk36xQkvoiYwxBLBQW3pump",
        token_symbol="TEST",
        token_name="Test Token",  # 添加缺失的字段
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
    
    try:
        # 测试旧方法（应该失败）
        try:
            old_dict = analysis_result.model_dump()
            json.dumps(old_dict)
            print("❌ 旧方法意外成功了")
        except TypeError as e:
            print(f"✅ 旧方法正确失败: {e}")
        
        # 测试新方法（应该成功）
        new_dict = analysis_result.to_json_dict()
        json_str = json.dumps(new_dict)
        print(f"✅ 新方法成功: JSON长度 {len(json_str)} 字符")
        
        # 验证反序列化
        parsed = json.loads(json_str)
        print(f"✅ 反序列化成功: analysis_started_at = {parsed['analysis_started_at']}")
        
        return True
        
    except Exception as e:
        print(f"❌ AnalysisResult序列化测试失败: {e}")
        return False

def test_message_queue_task_data():
    """测试消息队列任务数据的序列化"""
    print("\n🧪 测试消息队列任务数据序列化...")
    
    # 模拟消息队列中的任务数据结构
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
    
    # 模拟message_queue.add_analysis_task中的数据结构
    task_data = {
        "token_data": token_data.to_json_dict(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "task_id": f"{token_data.mint}_test_uuid"
    }
    
    try:
        json_str = json.dumps(task_data)
        print(f"✅ 任务数据序列化成功: JSON长度 {len(json_str)} 字符")
        
        # 验证反序列化
        parsed = json.loads(json_str)
        print(f"✅ 反序列化成功: task_id = {parsed['task_id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 任务数据序列化测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("🚀 开始JSON序列化修复验证测试")
    print("=" * 50)
    
    tests = [
        test_token_data_serialization,
        test_analysis_result_serialization,
        test_message_queue_task_data
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！JSON序列化问题已修复")
        return 0
    else:
        print("❌ 部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    exit(main())
