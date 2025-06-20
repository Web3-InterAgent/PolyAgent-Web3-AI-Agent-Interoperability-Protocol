from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.toolkits import MCPToolkit
import sys
import os
import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from AgentCore.config import config

@dataclass
class ConversationTurn:
    """对话轮次数据结构"""
    user_input: str
    ai_response: str
    timestamp: datetime

class ConversationManager:
    """对话管理器"""
    
    def __init__(self, max_history: int = 10):
        self.conversation_history: List[ConversationTurn] = []
        self.max_history = max_history
    
    def add_turn(self, user_input: str, ai_response: str):
        """添加对话轮次"""
        turn = ConversationTurn(
            user_input=user_input,
            ai_response=ai_response,
            timestamp=datetime.now()
        )
        
        self.conversation_history.append(turn)
        
        # 保持历史记录在限制范围内
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def get_context_summary(self) -> str:
        """获取对话上下文摘要"""
        if not self.conversation_history:
            return ""
        
        recent_turns = self.conversation_history[-3:]  # 最近3轮对话
        context_parts = []
        
        for turn in recent_turns:
            context_parts.append(f"用户: {turn.user_input}")
            context_parts.append(f"助手: {turn.ai_response[:100]}...")  # 截取前100字符
        
        return "\n".join(context_parts)

class YouxuanShoppingAgent:
    def __init__(self):
        # 初始化模型
        self.model = None
        try:
            print("🔄 正在初始化AI模型...")
            self.model = ModelFactory.create(
                model_platform=ModelPlatformType.MODELSCOPE,
                model_type='Qwen/Qwen2.5-72B-Instruct',
                model_config_dict={'temperature': 0.2},
                api_key='9d3aed4d-eca1-4e0c-9805-cb923ccbbf21',
            )
            print("✅ AI模型初始化成功")
        except Exception as e:
            print(f"⚠️ AI模型初始化失败，将使用备用回复模式: {e}")
            # 不设置模型，直接使用备用回复
            self.model = None

        # MCP配置文件路径
        self.mcp_config_path = os.path.join(
            os.path.dirname(__file__), "..", "Mcp", "youxuan_server.json"
        )
        
        # 初始化组件
        self.conversation_manager = ConversationManager()
        self.chat_agent_with_tools = None  # 带工具的ChatAgent
        self.chat_agent_basic = None  # 基础ChatAgent（无工具）
        self.mcp_available = False  # MCP服务可用性标志
        self.mcp_tested = False  # 是否已经测试过MCP
        
        # 初始化时快速测试MCP可用性（异步方式）
        self._initial_mcp_test_done = False
        
        # 带MCP工具的系统提示词
        self.system_message_with_tools = """你是百度优选智能购物助手，专门帮助用户搜索商品、下单购买和售后服务。

## 重要说明
百度优选平台主要销售手机配件、数码周边产品，可能没有手机本身的库存。当用户搜索手机时，通常会返回相关配件。

## 可用工具说明

你有以下6个百度优选MCP工具可以使用：

### 1. mcp_youxuan-mcp_spu_list - 商品检索
- 用途：根据关键词搜索商品
- 必需参数：keyWord (string) - 搜索关键词
- 可选参数：pageNum (int) - 页码，默认1；pageSize (int) - 每页数量，默认10，最大20
- 示例调用：搜索"iPhone手机"时使用参数 keyWord: "iPhone"

### 2. mcp_youxuan-mcp_spu_detail - 商品详情
- 用途：查询商品详细信息
- 必需参数：spuId (long) - 商品ID
- 示例调用：查看商品ID为665811的详情

### 3. mcp_youxuan-mcp_order_create - 创建订单
- 用途：为用户下单购买商品
- 必需参数：skuId (long) - 商品规格ID，spuId (long) - 商品ID
- 可选参数：count (int) - 购买数量，默认1，最大99
- 示例调用：下单购买指定规格的商品

### 4. mcp_youxuan-mcp_order_history - 订单历史
- 用途：查询用户订单历史
- 可选参数：pageNum (int) - 页码，默认1；pageSize (int) - 每页数量，默认10，最大10
- 示例调用：查看用户的历史订单

### 5. mcp_youxuan-mcp_order_detail - 订单详情
- 用途：查询特定订单的详细信息
- 必需参数：orderId (long) - 订单ID
- 示例调用：查看特定订单的详细信息

### 6. mcp_youxuan-mcp_after_service - 售后服务
- 用途：查询订单是否可以申请售后
- 必需参数：orderId (long) - 订单ID
- 示例调用：申请售后服务

## 交互原则

- 根据用户需求自动调用相应的MCP工具获取真实数据
- 当搜索结果不匹配用户需求时，主动说明并提供建议
- 保持对话连贯性，记住用户的偏好和历史
- 使用中文与用户交流，提供友好的购物体验
- 当用户搜索手机但只找到配件时，诚实告知平台商品情况

请根据用户的具体需求，智能调用工具，提供最佳的购物体验。"""

        # 基础对话系统提示词（无工具时使用）
        self.system_message_basic = """你是百度优选智能购物助手，虽然当前无法连接到百度优选服务，但我仍然可以为你提供购物建议和咨询服务。

## 当前状态
- 百度优选服务暂时不可用，无法进行实时商品搜索和下单
- 但我可以为你提供：
  - 购物建议和产品推荐
  - 商品选购知识分享
  - 品牌对比分析
  - 购物经验交流
  - 售后问题咨询建议

## 交互原则
- 基于我的知识库为你提供有用的购物信息
- 保持对话连贯性，记住你的偏好和需求
- 当服务恢复时，我会及时告知你
- 使用中文与你交流，提供友好的购物体验

请告诉我你的购物需求，我会尽力为你提供帮助！"""

        print("🤖 YouxuanShoppingAgent 初始化完成")

    async def _quick_mcp_test(self) -> bool:
        """快速测试MCP可用性（5秒超时）"""
        try:
            print("🔍 快速测试MCP服务可用性...")
            
            # 使用很短的超时时间进行快速测试
            async def _quick_test():
                async with MCPToolkit(config_path=self.mcp_config_path) as mcp_toolkit:
                    tools = mcp_toolkit.get_tools()
                    return len(tools) > 0
            
            result = await asyncio.wait_for(_quick_test(), timeout=5.0)
            if result:
                print("✅ MCP服务快速测试：可用")
                return True
            else:
                print("⚠️ MCP服务快速测试：无工具")
                return False
                
        except asyncio.TimeoutError:
            print("⏰ MCP服务快速测试：超时，判定为不可用")
            return False
        except Exception as e:
            print(f"❌ MCP服务快速测试：失败 - {e}")
            return False

    async def _test_mcp_availability(self) -> bool:
        """测试MCP服务可用性"""
        try:
            # 尝试连接MCP服务
            async with MCPToolkit(config_path=self.mcp_config_path) as mcp_toolkit:
                tools = mcp_toolkit.get_tools()
                if tools and len(tools) > 0:
                    print(f"✅ MCP服务可用，加载了 {len(tools)} 个工具")
                    return True
                else:
                    print("⚠️ MCP服务连接成功但无可用工具")
                    return False
        except Exception as e:
            print(f"❌ MCP服务不可用: {e}")
            return False

    async def _initialize_chat_agent_with_tools(self, mcp_toolkit):
        """初始化带工具的ChatAgent"""
        if self.chat_agent_with_tools is None:
            tools = mcp_toolkit.get_tools()
            self.chat_agent_with_tools = ChatAgent(
                system_message=self.system_message_with_tools,
                model=self.model,
                token_limit=32768,
                tools=tools,
                output_language="zh"
            )
            print(f"✅ 带工具的ChatAgent 初始化完成，加载了 {len(tools)} 个工具")

    async def _initialize_basic_chat_agent(self):
        """初始化基础ChatAgent（无工具）"""
        if self.chat_agent_basic is None and self.model is not None:
            try:
                print("🔄 正在初始化基础ChatAgent...")
                self.chat_agent_basic = ChatAgent(
                    system_message=self.system_message_basic,
                    model=self.model,
                    token_limit=32768,
                    tools=[],  # 无工具
                    output_language="zh"
                )
                print("✅ 基础ChatAgent初始化完成（无工具模式）")
            except Exception as e:
                print(f"❌ 基础ChatAgent初始化失败: {e}")
                self.chat_agent_basic = None

    async def _process_with_mcp(self, enhanced_input: str) -> str:
        """使用MCP工具处理请求"""
        import asyncio
        
        async def _mcp_task():
            async with MCPToolkit(config_path=self.mcp_config_path) as mcp_toolkit:
                await self._initialize_chat_agent_with_tools(mcp_toolkit)
                
                print("🤖 ChatAgent 正在使用MCP工具处理请求...")
                response = await self.chat_agent_with_tools.astep(enhanced_input)
                
                if response and response.msgs:
                    return response.msgs[0].content
                else:
                    return "抱歉，我暂时无法处理您的请求。"
        
        try:
            # 设置20秒超时时间来快速失败
            result = await asyncio.wait_for(_mcp_task(), timeout=20.0)
            return result
                    
        except (Exception, asyncio.CancelledError, asyncio.TimeoutError) as e:
            print(f"❌ MCP处理失败: {e}")
            raise e

    async def _process_basic(self, enhanced_input: str) -> str:
        """基础模式处理请求（无工具）"""
        try:
            # 如果模型不可用，直接返回友好回复
            if self.model is None:
                return self._get_fallback_response(enhanced_input)
            
            await self._initialize_basic_chat_agent()
            
            if self.chat_agent_basic is None:
                return self._get_fallback_response(enhanced_input)
            
            print("🤖 ChatAgent 正在使用基础模式处理请求...")
            
            # 添加超时处理
            try:
                response = await asyncio.wait_for(
                    self.chat_agent_basic.astep(enhanced_input), 
                    timeout=30.0  # 30秒超时
                )
                
                if response and response.msgs and len(response.msgs) > 0:
                    return response.msgs[0].content
                else:
                    return self._get_fallback_response(enhanced_input)
                    
            except asyncio.TimeoutError:
                print("⏰ 基础模式处理超时")
                return self._get_fallback_response(enhanced_input)
                
        except Exception as e:
            print(f"❌ 基础模式处理失败: {e}")
            import traceback
            print(f"🔍 详细错误: {traceback.format_exc()}")
            return self._get_fallback_response(enhanced_input)

    def _get_fallback_response(self, user_input: str) -> str:
        """生成友好的备用回复"""
        # 简单的关键词匹配来提供相关建议
        user_input_lower = user_input.lower()
        
        if any(keyword in user_input_lower for keyword in ['手机', 'iphone', '华为', '小米', '苹果']):
            return f"""您好！关于您询问的"{user_input}"，我很乐意为您提供建议：

📱 **手机选购建议**：
• **预算考虑**：根据您的预算选择合适价位的产品
• **品牌对比**：苹果注重系统体验，华为在拍照和信号方面表现优秀，小米性价比较高
• **使用需求**：游戏用户可考虑高刷新率屏幕，商务用户注重续航和信号
• **购买渠道**：建议选择官方渠道或信誉良好的商家

虽然当前无法连接到实时商品库，但我可以基于经验为您分析不同品牌和型号的特点。请告诉我您的具体需求和预算范围！"""

        elif any(keyword in user_input_lower for keyword in ['订单', '购买', '下单', '买']):
            return f"""关于您的购买需求"{user_input}"，我为您提供以下建议：

🛒 **购买流程建议**：
• **商品比较**：对比不同商家的价格、评价和服务
• **支付安全**：选择安全的支付方式
• **物流查询**：关注商品发货和配送时间
• **售后保障**：了解退换货政策和质保服务

虽然当前服务暂时不稳定，但我建议您：
1. 明确具体需求和预算
2. 多平台比价
3. 查看用户评价
4. 关注商家信誉

有什么具体想了解的吗？"""

        elif any(keyword in user_input_lower for keyword in ['价格', '多少钱', '便宜', '贵']):
            return f"""关于价格咨询"{user_input}"，我为您分析：

💰 **价格参考建议**：
• **市场行情**：建议多平台比较当前市场价格
• **促销活动**：关注节日促销和品牌官方活动
• **性价比**：不只看价格，还要考虑产品质量和服务
• **预算规划**：根据实际需求制定合理预算

虽然我现在无法查询实时价格，但建议您：
1. 在多个购物平台对比
2. 关注用户评价和销量
3. 考虑官方渠道的保障
4. 留意促销时机

请告诉我您想了解哪个具体产品的价格？"""

        else:
            return f"""您好！关于您的问题"{user_input}"，我很乐意帮助您：

🤖 **购物助手服务**：
虽然当前技术服务不太稳定，但我仍然可以为您提供：
• 商品选购建议和经验分享
• 品牌对比和特点分析  
• 购物流程指导
• 价格参考和省钱技巧

📝 **使用建议**：
• 描述具体需求（如：想买什么类型的商品）
• 说明预算范围
• 告诉我使用场景和偏好

请告诉我您具体想了解什么，或者有什么购物需求？我会基于经验为您提供实用的建议！"""

    async def process_request(self, user_input: str) -> str:
        """处理用户请求，支持MCP降级机制"""
        try:
            print(f"🔍 处理用户请求: {user_input}")
            
            # 获取对话上下文
            context_summary = self.conversation_manager.get_context_summary()
            
            # 构建包含上下文的用户输入
            if context_summary:
                enhanced_input = f"""用户当前请求: {user_input}

最近对话上下文:
{context_summary}

请根据以上信息，结合对话历史为用户提供帮助。"""
            else:
                enhanced_input = user_input
            
            ai_response = ""
            
            # 首次请求时进行快速MCP测试
            if not self._initial_mcp_test_done:
                self._initial_mcp_test_done = True
                print("🔍 首次请求，进行快速MCP可用性检测...")
                mcp_available = await self._quick_mcp_test()
                self.mcp_available = mcp_available
                self.mcp_tested = True
                print(f"🔧 MCP服务状态：{'可用' if mcp_available else '不可用'}")
            
            # 根据MCP测试结果决定使用哪种模式
            if self.mcp_tested and not self.mcp_available:
                # MCP已测试且不可用，直接使用基础模式
                print("🔧 使用基础模式（MCP不可用）")
                basic_enhanced_input = f"""用户请求: {user_input}

{context_summary if context_summary else ""}"""
                
                ai_response = await self._process_basic(basic_enhanced_input)
                
            else:
                # MCP可用，尝试使用MCP工具
                try:
                    ai_response = await self._process_with_mcp(enhanced_input)
                    self.mcp_available = True
                    print("✅ MCP模式响应成功")
                    
                except Exception as mcp_error:
                    print(f"⚠️ MCP模式失败，切换到基础模式: {mcp_error}")
                    self.mcp_available = False
                    
                    # 降级到基础模式
                    basic_enhanced_input = f"""用户请求: {user_input}

{context_summary if context_summary else ""}

注意：当前百度优选服务不可用，请基于你的知识为用户提供购物建议。"""
                    
                    ai_response = await self._process_basic(basic_enhanced_input)
                    
                    # 在响应前添加服务状态说明
                    if ai_response and not ai_response.startswith("抱歉") and not ai_response.startswith("🔧"):
                        ai_response = f"🔧 当前百度优选服务暂时不可用，我将基于知识库为您提供建议：\n\n{ai_response}"
            
            # 如果仍然没有响应，提供默认回复
            if not ai_response or ai_response.strip() == "":
                ai_response = "您好！我是百度优选购物助手。虽然当前服务不太稳定，但我很乐意为您提供购物建议。请告诉我您想了解什么商品，或者有什么购物需求？"
            
            # 记录对话历史
            self.conversation_manager.add_turn(user_input, ai_response)
            
            print("✅ 响应生成完成")
            return ai_response
            
        except Exception as e:
            print(f"❌ 处理请求时出错: {e}")
            import traceback
            print(f"🔍 详细错误信息: {traceback.format_exc()}")
            
            # 提供友好的错误响应
            error_response = f"""抱歉，我遇到了一些技术问题。让我为您提供一个简单的回复：

您的问题是：{user_input}

虽然当前无法连接到完整的购物服务，但我建议您：
1. 如果是商品咨询，我可以基于常识为您分析
2. 如果需要下单，建议稍后重试
3. 如果有其他问题，请尽管询问

请告诉我您具体想了解什么，我会尽力帮助您！"""

            # 即使出错也要记录对话
            self.conversation_manager.add_turn(user_input, error_response)
            return error_response

    # 为了兼容现有代码，保留smart_route_request方法
    async def smart_route_request(self, user_input: str) -> str:
        """兼容性方法，直接调用process_request"""
        return await self.process_request(user_input)

    def get_conversation_history(self) -> List[ConversationTurn]:
        """获取对话历史"""
        return self.conversation_manager.conversation_history

    def clear_conversation_history(self):
        """清除对话历史"""
        self.conversation_manager.conversation_history.clear()
        # 重置ChatAgent以开始新对话
        self.chat_agent_with_tools = None
        self.chat_agent_basic = None
        # 重置MCP状态，允许重新测试
        self.mcp_tested = False
        self.mcp_available = False
        print("🧹 对话历史已清除，ChatAgent已重置，MCP状态已重置")

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "mcp_available": self.mcp_available,
            "conversation_turns": len(self.conversation_manager.conversation_history),
            "model_available": self.model is not None
        }

# 全局清理函数
async def cleanup_connections():
    """清理连接"""
    print("🧹 连接清理完成")

if __name__ == "__main__":
    async def test_agent():
        agent = YouxuanShoppingAgent()
        
        # 测试多轮对话
        print("=== 测试多轮对话 ===")
        
        # 第一轮：搜索苹果相关产品
        print("\n--- 第一轮对话 ---")
        result1 = await agent.process_request("我想买苹果手机")
        print("AI回复:", result1)
        
        # 第二轮：基于第一轮结果继续对话
        print("\n--- 第二轮对话 ---")
        result2 = await agent.process_request("那有什么苹果的配件推荐吗？")
        print("AI回复:", result2)
        
        # 第三轮：询问订单
        print("\n--- 第三轮对话 ---")
        result3 = await agent.process_request("我想看看我的订单历史")
        print("AI回复:", result3)
        
        # 查看服务状态
        print("\n--- 服务状态 ---")
        status = agent.get_service_status()
        print("服务状态:", status)

    asyncio.run(test_agent()) 