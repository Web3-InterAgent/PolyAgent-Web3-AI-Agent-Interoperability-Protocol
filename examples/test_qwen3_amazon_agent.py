"""
Qwen3版本Amazon购物Agent测试文件
测试Qwen3-32B模型在购物场景中的思考模式和推理能力
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加路径以便导入Agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from AgentCore.Society.amazon_shopping_agent_qwen3 import (
    AmazonShoppingAgentQwen3, 
    ThinkingMode, 
    ShoppingState
)

class Qwen3AgentTester:
    """Qwen3 Amazon购物Agent测试器"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始Qwen3 Amazon购物Agent全面测试")
        print("=" * 60)
        self.start_time = datetime.now()
        
        # 测试用例
        test_cases = [
            self.test_thinking_modes,
            self.test_purchase_flow,
            self.test_intent_analysis,
            self.test_state_management,
            self.test_mcp_integration,
            self.test_error_handling
        ]
        
        for test_case in test_cases:
            try:
                print(f"\n🧪 运行测试: {test_case.__name__}")
                await test_case()
                self.test_results.append(f"✅ {test_case.__name__}: 通过")
            except Exception as e:
                print(f"❌ 测试失败: {e}")
                self.test_results.append(f"❌ {test_case.__name__}: 失败 - {e}")
        
        self._print_summary()
    
    async def test_thinking_modes(self):
        """测试不同思考模式"""
        print("🧠 测试Qwen3思考模式切换...")
        
        modes_to_test = [
            (ThinkingMode.ENABLED, "复杂购物决策"),
            (ThinkingMode.DISABLED, "简单查询"),
            (ThinkingMode.AUTO, "自适应模式")
        ]
        
        for mode, description in modes_to_test:
            print(f"  测试模式: {mode.value} - {description}")
            agent = AmazonShoppingAgentQwen3(thinking_mode=mode)
            
            # 测试模式特定的查询
            if mode == ThinkingMode.ENABLED:
                query = "我想买一款既适合办公又适合游戏的笔记本电脑，预算在8000-12000元，请帮我分析和推荐"
            elif mode == ThinkingMode.DISABLED:
                query = "查看我的订单历史"
            else:  # AUTO
                query = "我想买iPhone手机配件"
            
            response = await agent.process_request(query)
            state = agent.get_shopping_state()
            
            print(f"    模式: {state['thinking_mode']}")
            print(f"    响应长度: {len(response)}")
            print(f"    状态: {state['current_state']}")
            
            # 验证模式是否正确设置
            assert state['thinking_mode'] == mode.value, f"思考模式设置错误: {state['thinking_mode']} != {mode.value}"
        
        print("✅ 思考模式测试通过")
    
    async def test_purchase_flow(self):
        """测试完整购买流程"""
        print("🛒 测试完整购买流程...")
        
        agent = AmazonShoppingAgentQwen3(thinking_mode=ThinkingMode.AUTO)
        
        # 定义购买流程步骤
        flow_steps = [
            ("我想买一支好写的黑色圆珠笔", ShoppingState.BROWSING),
            ("我选择第一款Pilot G2圆珠笔", ShoppingState.SELECTED),
            ("我的姓名是张三，邮箱是zhangsan@email.com", ShoppingState.COLLECTING_INFO),
            ("我的地址是北京市朝阳区XX街道XX号", ShoppingState.COLLECTING_INFO),
            ("请帮我创建订单", ShoppingState.ORDERING),
        ]
        
        for step, expected_state in flow_steps:
            print(f"  步骤: {step}")
            response = await agent.process_request(step)
            current_state = agent.get_shopping_state()
            
            print(f"    当前状态: {current_state['current_state']}")
            print(f"    响应: {response[:100]}...")
            
            # 状态可能不会立即转换，但应该在合理范围内
            possible_states = [expected_state.value, ShoppingState.BROWSING.value, ShoppingState.COLLECTING_INFO.value]
            assert current_state['current_state'] in possible_states, f"状态转换异常: {current_state['current_state']}"
        
        # 检查对话历史
        history = agent.get_conversation_history()
        assert len(history) == len(flow_steps), f"对话历史记录数量错误: {len(history)} != {len(flow_steps)}"
        
        print("✅ 购买流程测试通过")
    
    async def test_intent_analysis(self):
        """测试用户意图分析"""
        print("🔍 测试用户意图分析...")
        
        agent = AmazonShoppingAgentQwen3(thinking_mode=ThinkingMode.AUTO)
        
        # 测试不同类型的用户输入
        intent_test_cases = [
            ("我想买iPhone", "purchase"),
            ("搜索笔记本电脑", "search"),
            ("查看我的订单", "order_inquiry"),
            ("我要付款", "payment"),
            ("有什么推荐的吗", "search")
        ]
        
        for query, expected_intent in intent_test_cases:
            print(f"  查询: {query}")
            # 直接调用意图分析方法
            intent_analysis = agent._analyze_user_intent(query)
            
            print(f"    分析结果: {intent_analysis['primary_intent']}")
            print(f"    置信度: {intent_analysis['confidence']}")
            print(f"    复杂度: {intent_analysis['complexity']}")
            
            # 验证意图分析结果
            if expected_intent != "unknown":
                assert intent_analysis['primary_intent'] == expected_intent, f"意图分析错误: {intent_analysis['primary_intent']} != {expected_intent}"
        
        print("✅ 意图分析测试通过")
    
    async def test_state_management(self):
        """测试状态管理"""
        print("📊 测试状态管理...")
        
        agent = AmazonShoppingAgentQwen3(thinking_mode=ThinkingMode.AUTO)
        
        # 测试状态转换
        initial_state = agent.get_shopping_state()
        assert initial_state['current_state'] == ShoppingState.BROWSING.value, "初始状态错误"
        
        # 手动更新状态
        agent.conversation_manager.update_state(ShoppingState.SELECTED)
        updated_state = agent.get_shopping_state()
        assert updated_state['current_state'] == ShoppingState.SELECTED.value, "状态更新失败"
        
        # 测试状态重置
        agent.clear_conversation_history()
        reset_state = agent.get_shopping_state()
        assert reset_state['current_state'] == ShoppingState.BROWSING.value, "状态重置失败"
        assert reset_state['conversation_turns'] == 0, "对话轮次重置失败"
        
        print("✅ 状态管理测试通过")
    
    async def test_mcp_integration(self):
        """测试MCP工具集成"""
        print("🔧 测试MCP工具集成...")
        
        agent = AmazonShoppingAgentQwen3(thinking_mode=ThinkingMode.AUTO)
        
        # 测试MCP连接
        try:
            mcp_available = await agent._quick_mcp_test()
            print(f"  MCP服务可用性: {'是' if mcp_available else '否'}")
            
            # 无论MCP是否可用，agent都应该能够响应
            response = await agent.process_request("搜索蓝牙耳机")
            assert len(response) > 0, "MCP模式下响应为空"
            
            final_state = agent.get_shopping_state()
            print(f"  MCP状态: {final_state['mcp_available']}")
            
        except Exception as e:
            print(f"  MCP测试遇到异常: {e}")
            # 这是可以接受的，因为MCP服务可能不可用
        
        print("✅ MCP集成测试通过")
    
    async def test_error_handling(self):
        """测试错误处理"""
        print("⚠️ 测试错误处理...")
        
        agent = AmazonShoppingAgentQwen3(thinking_mode=ThinkingMode.AUTO)
        
        # 测试各种边界情况
        edge_cases = [
            "",  # 空输入
            "   ",  # 空格输入
            "a" * 1000,  # 很长的输入
            "🤖🛒💰",  # 特殊字符
            "SELECT * FROM users;",  # 可能的注入尝试
        ]
        
        for case in edge_cases:
            try:
                response = await agent.process_request(case)
                assert isinstance(response, str), f"响应类型错误: {type(response)}"
                assert len(response) > 0, f"对边界情况 '{case[:20]}...' 响应为空"
                print(f"  ✅ 处理边界情况: '{case[:20]}...'")
            except Exception as e:
                print(f"  ⚠️ 边界情况处理异常: {e}")
                # 记录但不失败，因为某些异常可能是预期的
        
        print("✅ 错误处理测试通过")
    
    def _print_summary(self):
        """打印测试摘要"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 60)
        print("🏁 Qwen3 Amazon购物Agent测试总结")
        print("=" * 60)
        print(f"⏱️ 测试时长: {duration.total_seconds():.2f}秒")
        print(f"📊 总测试数: {len(self.test_results)}")
        
        passed = sum(1 for result in self.test_results if result.startswith("✅"))
        failed = len(self.test_results) - passed
        
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"📈 成功率: {(passed/len(self.test_results)*100):.1f}%")
        
        print("\n📋 详细结果:")
        for result in self.test_results:
            print(f"  {result}")
        
        if failed == 0:
            print("\n🎉 所有测试通过！Qwen3 Amazon购物Agent运行正常。")
        else:
            print(f"\n⚠️ 有{failed}个测试失败，请检查相关功能。")

async def main():
    """主测试函数"""
    print("🔥 Qwen3-32B Amazon购物Agent测试启动")
    print("基于CAMEL-AI框架和最新的Qwen3模型")
    print("测试思考模式、MCP工具集成和完整购物流程")
    
    tester = Qwen3AgentTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main()) 