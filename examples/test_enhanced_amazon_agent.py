#!/usr/bin/env python3
"""
增强版Amazon购物Agent测试脚本
测试Amazon MCP和Fewsats MCP的完整集成功能
"""

import asyncio
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from AgentCore.Society.amazon_shopping_agent import AmazonShoppingAgent, ShoppingState

class AmazonAgentTester:
    def __init__(self):
        self.agent = None
        self.test_results = []
        
    async def setup(self):
        """初始化测试环境"""
        print("🔧 初始化Amazon购物Agent测试环境...")
        self.agent = AmazonShoppingAgent()
        print("✅ 测试环境初始化完成\n")
        
    async def test_basic_conversation(self):
        """测试基础对话功能"""
        print("=== 测试1: 基础对话功能 ===")
        
        test_inputs = [
            "你好，我想在Amazon上买些东西",
            "我需要搜索黑色钢笔",
            "请帮我查询钱包余额",
            "谢谢你的帮助"
        ]
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n📝 测试输入 {i}: {user_input}")
            try:
                response = await self.agent.process_request(user_input)
                print(f"🤖 AI回复: {response[:200]}...")
                print(f"📊 当前状态: {self.agent.current_state.value}")
            except Exception as e:
                print(f"❌ 错误: {e}")
                
        print("✅ 基础对话测试完成\n")
        
    async def test_shopping_flow(self):
        """测试完整购物流程"""
        print("=== 测试2: 完整购物流程 ===")
        
        # 清除历史记录，开始新的购物流程
        self.agent.clear_conversation_history()
        
        shopping_steps = [
            ("搜索商品", "我想买一支好用的黑色钢笔"),
            ("查看商品", "请显示搜索结果"),
            ("选择商品", "我要选择第一个商品"),
            ("提供信息", "我的姓名是张三，邮箱zhangsan@email.com，地址是北京市朝阳区建国路123号，邮编100025"),
            ("查询余额", "请查询我的钱包余额"),
            ("获取报价", "请为我获取支付报价"),
            ("查询订单", "查询我的订单状态")
        ]
        
        for step_name, user_input in shopping_steps:
            print(f"\n🛒 {step_name}: {user_input}")
            try:
                response = await self.agent.process_request(user_input)
                print(f"🤖 AI回复: {response[:200]}...")
                
                # 显示购物进度
                progress = self.agent.get_shopping_progress()
                print(f"📈 购物进度: {progress['progress_percentage']}% - {progress['current_state']}")
                print(f"💡 下一步: {progress['next_step']}")
                
                # 模拟短暂延迟
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ 错误: {e}")
                
        print("✅ 购物流程测试完成\n")
        
    async def test_intent_analysis(self):
        """测试用户意图分析"""
        print("=== 测试3: 用户意图分析 ===")
        
        test_phrases = [
            "我想搜索笔记本电脑",
            "查询我的余额",
            "我要买这个商品",
            "查看我的订单",
            "帮我支付",
            "选择第二个商品",
            "这个不太好，换个别的"
        ]
        
        for phrase in test_phrases:
            intent = self.agent.analyze_user_intent(phrase)
            print(f"📝 输入: {phrase}")
            print(f"🎯 意图: {intent['intent']} (置信度: {intent['confidence']})")
            print(f"🔧 推荐工具: {intent['recommended_tools']}")
            print(f"📊 建议状态: {intent['next_state'].value}\n")
            
        print("✅ 意图分析测试完成\n")
        
    async def test_error_handling(self):
        """测试错误处理"""
        print("=== 测试4: 错误处理 ===")
        
        # 测试各种可能的错误场景
        error_scenarios = [
            "搜索一个非常奇怪的商品名称",
            "使用错误的命令格式",
            "",  # 空输入
            "支付一个不存在的订单",
        ]
        
        for scenario in error_scenarios:
            if scenario:  # 跳过空字符串的打印
                print(f"\n⚠️ 错误场景: {scenario}")
            try:
                response = await self.agent.process_request(scenario)
                print(f"🤖 处理结果: {response[:150]}...")
            except Exception as e:
                print(f"🛡️ 异常捕获: {e}")
                
        print("✅ 错误处理测试完成\n")
        
    async def test_service_status(self):
        """测试服务状态监控"""
        print("=== 测试5: 服务状态监控 ===")
        
        # 获取服务状态
        status = self.agent.get_service_status()
        print("📊 服务状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
            
        # 获取购物进度
        progress = self.agent.get_shopping_progress()
        print("\n📈 购物进度:")
        for key, value in progress.items():
            print(f"  {key}: {value}")
            
        # 获取建议
        suggestion = self.agent.suggest_next_action()
        print(f"\n💡 操作建议: {suggestion}")
        
        print("✅ 服务状态测试完成\n")
        
    async def test_conversation_memory(self):
        """测试对话记忆功能"""
        print("=== 测试6: 对话记忆功能 ===")
        
        # 开始新对话
        self.agent.clear_conversation_history()
        
        conversation = [
            "我想买一本书",
            "关于人工智能的书",
            "价格在50美元以下的",
            "你记得我刚才说想买什么吗？",
            "我刚才提到的价格范围是多少？"
        ]
        
        for i, message in enumerate(conversation, 1):
            print(f"\n💬 对话轮次 {i}: {message}")
            response = await self.agent.process_request(message)
            print(f"🤖 AI回复: {response[:200]}...")
            
            # 显示对话历史数量
            history_count = len(self.agent.get_conversation_history())
            print(f"📚 对话历史: {history_count} 轮")
            
        print("✅ 对话记忆测试完成\n")
        
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行Amazon购物Agent完整测试套件")
        print("=" * 60)
        
        start_time = datetime.now()
        
        try:
            await self.setup()
            await self.test_basic_conversation()
            await self.test_shopping_flow()
            await self.test_intent_analysis()
            await self.test_error_handling()
            await self.test_service_status()
            await self.test_conversation_memory()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("🎉 所有测试完成!")
            print(f"⏰ 总耗时: {duration.total_seconds():.2f} 秒")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n⏹️ 测试被用户中断")
        except Exception as e:
            print(f"\n❌ 测试过程中出现异常: {e}")
            import traceback
            traceback.print_exc()
            
    async def interactive_test(self):
        """交互式测试模式"""
        print("🎮 进入交互式测试模式")
        print("输入 'quit' 或 'exit' 退出，输入 'clear' 清除历史，输入 'status' 查看状态")
        print("-" * 50)
        
        await self.setup()
        
        while True:
            try:
                user_input = input("\n👤 您: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 再见！")
                    break
                elif user_input.lower() == 'clear':
                    self.agent.clear_conversation_history()
                    print("🧹 对话历史已清除")
                    continue
                elif user_input.lower() == 'status':
                    status = self.agent.get_service_status()
                    progress = self.agent.get_shopping_progress()
                    print("📊 服务状态:", status)
                    print("📈 购物进度:", progress)
                    continue
                elif not user_input:
                    continue
                    
                # 处理用户输入
                print("🤖 思考中...")
                response = await self.agent.process_request(user_input)
                print(f"🤖 AI助手: {response}")
                
                # 显示当前状态
                print(f"📊 当前状态: {self.agent.current_state.value}")
                
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 处理出错: {e}")

async def main():
    """主函数"""
    tester = AmazonAgentTester()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await tester.interactive_test()
    else:
        await tester.run_all_tests()

if __name__ == "__main__":
    print("🛍️ Amazon购物Agent增强版测试工具")
    print("使用 --interactive 参数进入交互模式")
    print()
    
    asyncio.run(main()) 