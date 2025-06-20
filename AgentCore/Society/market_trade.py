# file: market_trade_server.py
import re
import os
import sys
import asyncio
from string import Template

# --- A2A 和 CAMEL 库导入 ---
from python_a2a import A2AServer, run_server, AgentCard, AgentSkill, TaskStatus, TaskState
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from camel.toolkits import MCPToolkit

# --- 项目内部模块导入 ---
# 路径设置，确保能找到项目核心模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from AgentCore.Tools.iotextoken_toolkit import IotexTokenToolkit
from AgentCore.config import config


# ==============================================================================
#  将 AgentManager 的完整实现迁移到这里
# ==============================================================================
class AgentManager:
    """
    这个类包含了所有原始的交易、支付、区块链和故事生成逻辑。
    我们把它作为服务器核心功能的基础。
    """
    def __init__(self):
        # --- 区块链和合约配置 ---
        self.estnet_rpc = "https://babel-api.testnet.iotex.io"
        self.chain_id = 4690
        self.ERC20_ABI = [
            {"constant": False, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_from", "type": "address"}, {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transferFrom", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
        ]

        # --- 模型初始化 ---
        print("🧠 [MarketTradeServer] Initializing the core AI model...")
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.MODELSCOPE,
            model_type='Qwen/Qwen2.5-72B-Instruct',
            model_config_dict={'temperature': 0.2},
            api_key='9d3aed4d-eca1-4e0c-9805-cb923ccbbf21',
        )
        print("✅ [MarketTradeServer] AI model is ready.")

        # --- 子 Agent 初始化 ---
        print("🤖 [MarketTradeServer] Initializing sub-agents...")
        self.iotex_agent = ChatAgent(
            system_message="""
            You are a professional IoTeX testnet blockchain assistant with the following capabilities:

            =================
            ✅ Query Functions
            =================
            1. Query account IOTX balance  
            - Function: iotex_balance  
            - Parameters: wallet_address

            2. Query account ERC20 token balance  
            - Function: erc20_balance  
            - Parameters: wallet_address, token_contract_address

            3. Query ERC20 allowance  
            - Function: erc20_allowance  
            - Parameters: owner_address, spender_address, token_contract_address, [decimals] (optional)

            4. Query ERC20 contract information  
            - Function: erc20_contract_info  
            - Parameters: token_contract_address

            =================
            🛠️ Transaction Functions
            =================
            5. Approve ERC20 token usage  
            - Function: erc20_approve  
            - Parameters: private_key, spender_address, token_contract_address, amount, [decimals] (optional)

            6. Execute ERC20 transferFrom  
            - Function: erc20_transfer_from  
            - Parameters: private_key, token_contract_address, from_address, to_address, amount, [decimals] (optional)

            =================
            💬 Interaction Guidelines
            =================
            - For query operations, provide relevant addresses and contract addresses for ERC20 tokens
            - All on-chain write operations require confirmation before execution
            - For operations involving private keys, remind users about security - **never share private keys in plaintext**
            - All operations are limited to IoTeX testnet

            =======================
            📦 Default Parameters
            =======================
            # PolyAgent Token Contract (ERC20)
            polyagent_token_contract = "0xD3286E20Ff71438D9f6969828F7218af4A375e2f"

            # Sender Account
            Sender Address: "0xE4949a0339320cE9ec93c9d0836c260F23DFE8Ca"
            Sender Private Key: "e4ad52fbc8c6fe3f4069af70363b24ca4453dbf472d92f83a8adf38e8010991f"

            # Spender Account
            Spender Address: "0xf874871Bc0f99a06b5327F34AceAa80Ae71905DE"
            Spender Private Key: "3efe78303dcf8ea3355ef363f04eb442e000081fe66ebcebf5d9cf19f3ace8b8"

            # Default settings
            decimals = 18
            amount = 2

            =======================
            🤖 Execution Rules [Important]
            =======================
            You have all required parameters. When users request queries or transactions, select and execute the appropriate function directly based on the content. Unless users explicitly specify different values, use the default parameters above without asking for additional input.
            
            Respond in English and provide clear, professional explanations.
            """,
            model=self.model,
            token_limit=32768,
            tools=[*IotexTokenToolkit(self.estnet_rpc, self.ERC20_ABI, self.chain_id).get_tools()],
            output_language="en"
        )

        self.story_agent = ChatAgent(
            system_message="""    
            [System Notice] You have received 5 XRC20 tokens as a reward.

            Please create a stylized micro-story based on the user's request. Ensure the story begins by mentioning this event: "receiving 5 XRC20 tokens".

            Choose from styles like fantasy, sci-fi, mystery, fairy tale, or cyberpunk.

            User request: $user_demand

            Requirements:
            - Story must clearly mention "receiving 5 XRC20 tokens" at the beginning
            - Story should develop around this request, showing its significance or triggered events
            - Immersive writing style with clear background and concise character development
            - No paragraph breaks, around 150 words
            - Ending should be open or hint at larger developments

            Please generate the story in English.""",
            model=self.model,
            token_limit=32768,
            output_language="en"
        )
        print("✅ [MarketTradeServer] Sub-agents are ready.")

        # --- 状态跟踪 ---
        self.demo_step = 0
        self.demo_context = {
            "order_id": "ORDER20250107001",
            "amount_usd": 49.99,
            "amount_tokens": 49.99,
            "merchant_wallet": "0xf874871Bc0f99a06b5327F34AceAa80Ae71905DE",
            "user_wallet": "0xE4949a0339320cE9ec93c9d0836c260F23DFE8Ca",
            "usd_to_rmb_rate": 7.25,
            "download_link": "https://pan.baidu.com/s/1F4TgbbTrz4LbSifczoDcXg?pwd=6712"
        }

        # 初始化百度优选购物Agent
        self.youxuan_agent = YouxuanShoppingAgent()

    async def smart_route_request(self, user_input: str):
        user_input_lower = user_input.lower()
        
        course_keywords = ["purchase", "buy", "course", "want to buy", "learning", "training", "enroll", "python", "web", "ai", "machine learning"]
        if any(keyword in user_input_lower for keyword in course_keywords):
            return await self.handle_step1_create_order(user_input)
        
        if "confirm_payment" in user_input_lower:
            return await self.handle_step2_automated_payment(user_input)
        
        blockchain_keywords = ["balance", "query", "check", "iotex", "token", "blockchain", "wallet", "address"]
        if any(keyword in user_input_lower for keyword in blockchain_keywords):
            return await self.handle_blockchain_query(user_input)
        
        auth_keywords = ["authorize", "approve", "authorization", "allow", "permit", "allowance"]
        if any(keyword in user_input_lower for keyword in auth_keywords):
            return await self.handle_token_authorization(user_input)
        
        story_keywords = ["story", "create", "novel", "sci-fi", "fantasy", "cyberpunk", "received", "reward", "xrc20"]
        if any(keyword in user_input_lower for keyword in story_keywords):
            return await self.handle_creative_story(user_input)
        
        return await self.handle_general_query(user_input)

    async def handle_step1_create_order(self, user_input: str):
        print(f"(Creating Alipay Payment Order) for user: {user_input}")
        course_info = self.extract_course_info(user_input)
        payment_info = await self.run_alipay_query(
            f"Create a payment order for {course_info['price_rmb']:.2f} RMB to purchase {course_info['name']}, with order ID {self.demo_context['order_id']}"
        )
        return payment_info

    def extract_course_info(self, user_input):
        """从用户输入中提取或生成课程信息"""
        # 根据用户输入智能提取课程信息，这里使用示例数据
        if "python" in user_input.lower():
            return {
                "name": "Primary Python Course",
                "platform": "edX",
                "duration": "8 weeks",
                "level": "Beginner to Intermediate",
                "description": "Learn Python programming fundamentals through hands-on exercises and projects. This comprehensive course covers Python syntax, data structures, functions, and object-oriented programming concepts essential for modern development.",
                "price_usd": 49.99,
                "price_rmb": 49.99 * self.demo_context['usd_to_rmb_rate'],
                "url": "https://www.edx.org/learn/python",
                "instructor": "edX Professional Education",
                "certificate": "Verified Certificate Available"
            }
        elif "web" in user_input.lower() or "javascript" in user_input.lower():
            return {
                "name": "Full Stack Web Development Bootcamp",
                "platform": "edX",
                "duration": "12 weeks",
                "level": "Intermediate to Advanced",
                "description": "Learn to build complete web applications using modern technologies like React, Node.js, and MongoDB. Includes deployment and DevOps practices.",
                "price_usd": 89.99,
                "price_rmb": 89.99 * self.demo_context['usd_to_rmb_rate'],
                "url": "https://www.edx.org/learn/web-development",
                "instructor": "edX Professional Education",
                "certificate": "Professional Certificate"
            }
        else:
            # 默认课程
            return {
                "name": "AI & Machine Learning Fundamentals",
                "platform": "edX",
                "duration": "10 weeks",
                "level": "Beginner to Intermediate",
                "description": "Explore the fundamentals of artificial intelligence and machine learning. Learn to build and deploy ML models using Python, TensorFlow, and scikit-learn.",
                "price_usd": 69.99,
                "price_rmb": 69.99 * self.demo_context['usd_to_rmb_rate'],
                "url": "https://www.edx.org/learn/artificial-intelligence",
                "instructor": "edX Professional Education",
                "certificate": "Professional Certificate"
            }

    async def handle_step2_automated_payment(self, user_input: str):
        print(f"(Automated Payment Process - Frontend Handled) for user: {user_input}")
        return """<div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;"><strong>✅ Automated payment process started</strong><br>The frontend will handle the automated payment flow.</div>"""

    # file: market_trade.py

# ... (文件顶部的其他代码保持不变) ...
# 在 AgentManager 类内部:

    async def run_alipay_query(self, query: str):
        config_path = os.path.join(os.path.dirname(__file__), "..", "Mcp", "alipay_server.json")
        config_path = os.path.abspath(config_path)
        try:
            async with MCPToolkit(config_path=config_path) as mcp_toolkit:
                alipay_agent = ChatAgent(system_message="""
                    You are an Alipay Agent for a cross-border payment service. Your task is to create a payment order in Chinese Yuan (RMB) for a product priced in US Dollars.

                    **Action: Create Payment Order (`create_payment`)**
                    - When a user wants to pay, call the `create_payment` function.
                    - Use these exact parameters:
                        - `outTradeNo`: 'ORDER20250107001'
                        - `totalAmount`: '362.43'  (This is the RMB equivalent of $49.99 USD)
                        - `orderTitle`: 'PolyAgent edX Course - Primary Python'

                    **Response Format:**
                    - You MUST return an HTML block with a payment link. Use this exact format:
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="[支付链接]" class="alipay-payment-button" target="_blank" onclick="handleAlipayPayment(this)">Confirm Payment with Alipay</a>
                    </div>
                    
                    <div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
                        <strong>💡 Payment Instructions:</strong><br>
                        1. Click the button to open the Alipay payment page.
                    </div>
                    """, model=self.model, tools=[*mcp_toolkit.get_tools()], output_language="en")
                
                response = await alipay_agent.astep(query)
                
                # ========================= START: 第二次修复 =========================
                if not (response and response.msgs and response.msgs[0].content):
                    return "错误: Agent未能生成有效响应或响应内容为空。"

                # astep返回的response.msgs[0]通常包含了最终的、包含工具调用结果的完整内容
                final_content = response.msgs[0].content
                
                if 'alipaydev.com' not in final_content:
                     return f"错误: 未能在Agent的最终响应中找到支付宝支付链接。原始响应: {final_content}"

                # 使用正则表达式从Markdown链接格式中可靠地提取URL
                # 这个正则表达式现在直接作用于最终的完整内容字符串
                match = re.search(r'\((https?://[^\)]+alipaydev\.com[^\)]+)\)', final_content)
                if not match:
                    return f"错误: 无法从Agent响应中提取有效的支付宝URL: {final_content}"
                
                payment_url = match.group(1) # group(1) 捕获括号内的内容

                # 手动构建最终的HTML响应，嵌入提取到的URL
                html_response = f'''
<div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 16px; margin: 1rem 0; text-align: center;">
    <strong style="color: #A78BFA; font-size: 1.1em; display: block; margin-bottom: 12px;">您的支付宝支付订单已就绪。</strong>
    <p style="color: #94A3B8; font-size: 0.9em; margin-bottom: 16px;">请点击下方按钮完成支付。</p>
    <a href="{payment_url}" 
       class="alipay-payment-button" 
       target="_blank" 
       onclick="handleAlipayPayment(this)"
       style="display: inline-block; padding: 10px 24px; background: linear-gradient(90deg, #4A90E2, #0070BA); color: white; text-decoration: none; font-weight: bold; border-radius: 6px; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);">
       使用支付宝确认支付 (¥362.43)
    </a>
</div>
<div style="background: rgba(74, 144, 226, 0.1); border-left: 3px solid #4A90E2; padding: 12px; margin-top: 1rem; font-size: 0.9em; color: #94A3B8;">
    <strong>💡 后续步骤:</strong><br>
    支付成功后，系统将自动处理后续的稳定币转账和课程交付流程。
</div>
'''
                return html_response
                # ========================== END: 第二次修复 ==========================

        except Exception as e:
            # 捕获异常并打印，便于调试
            import traceback
            print(f"支付宝处理过程中出现错误: {str(e)}")
            traceback.print_exc() # 打印完整的错误堆栈
            return f"""❌ 支付宝处理错误

处理支付宝请求时发生错误: {str(e)}
请检查支付宝MCP服务器状态并重试。"""

# ... (类和文件的其余部分保持不变)   

    async def run_paypal_query(self, query: str):
        config_path = os.path.join(os.path.dirname(__file__), "..", "Mcp", "paypal_server.json")
        config_path = os.path.abspath(config_path)
        try:
            async with MCPToolkit(config_path=config_path) as mcp_toolkit:
                paypal_agent = ChatAgent(system_message="""
                      你是一个经验丰富的 Paypal 交易代理，负责协助用户完成以下操作：

                1. 创建发票（create_invoice）
                2. 查询订单状态（query_order）
                3. 处理退款请求（process_refund）

                请根据用户的具体需求使用合适的工具进行操作，确保金额、税费、折扣等计算准确，语言清晰专业。
                    """, model=self.model, tools=[*mcp_toolkit.get_tools()], output_language="en")
                response = await paypal_agent.astep(query)
                return response.msgs[0].content if response and response.msgs else "Unable to get PayPal response"
        except Exception as e:
            return f"""❌ PayPal Processing Error: {str(e)}"""
    
    # ... (run_amap_query, run_all, etc., can be kept or removed if not directly exposed via the router)

    async def handle_blockchain_query(self, user_input: str):
        response = self.iotex_agent.step(user_input)
        return f"""🔗 **IoTeX Blockchain Query Results**\n\n{response.msgs[0].content if response.msgs else "Query failed"}"""

    async def handle_token_authorization(self, user_input: str):
        response = self.iotex_agent.step(f"Please execute the following authorization operation: {user_input}")
        return f"""🔐 **Token Authorization Operation**\n\n{response.msgs[0].content if response.msgs else "Authorization failed"}"""

    async def handle_creative_story(self, user_input: str):
        story_template = Template(self.story_agent.system_message)
        formatted_system_message = story_template.safe_substitute(user_demand=user_input)
        self.story_agent.system_message = formatted_system_message
        response = self.story_agent.step("Please create a story based on my requirements")
        return f"""📖 **AI Creative Story**\n\n{response.msgs[0].content if response.msgs else "Story generation failed"}"""

    async def handle_general_query(self, user_input: str):
        return f"""🤖 **General Assistant Response**\n\nYour question: "{user_input}"\n\nI apologize, but I cannot understand your specific requirements at the moment... (rest of the message)"""


# ==============================================================================
#  A2A 服务器的实现
# ==============================================================================
class MarketTradeServer(A2AServer, AgentManager):
    """
    这个类是最终的A2A服务器。
    它通过多重继承，同时获得了 A2AServer 的网络服务能力 和 AgentManager 的业务逻辑能力。
    """
    def __init__(self, agent_card: AgentCard):
        # 1. 初始化 A2AServer 部分
        A2AServer.__init__(self, agent_card=agent_card)
        # 2. 初始化 AgentManager 部分 (包含了模型、子Agent等的创建)
        AgentManager.__init__(self)
        print("✅ MarketTradeServer fully initialized.")

    def handle_task(self, task):
        """
        这是 A2A 服务器的核心处理函数。
        当收到来自 app.py 的请求时，此方法会被调用。
        """
        text = task.message.get("content", {}).get("text", "")
        if not text:
            response_text = "Error: Received an empty request."
        else:
            print(f"📩 [MarketTradeServer] Received task: {text}")
            try:
                # ========================= START: 核心修复 =========================
                # 使用 asyncio.run() 来安全地运行异步函数。
                # 它会自动处理事件循环的创建和清理，避免资源泄露。
                response_text = asyncio.run(self.smart_route_request(text))
                # ========================== END: 核心修复 ==========================
                
                print("💬 [MarketTradeServer] Smart router processing complete.")
            except Exception as e:
                import traceback
                print(f"❌ [MarketTradeServer] Error during smart_route_request: {e}")
                traceback.print_exc()
                response_text = f"Error processing request in MarketTradeServer: {e}"

        # 将最终结果打包成 A2A 响应
        task.artifacts = [{"parts": [{"type": "text", "text": str(response_text)}]}]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task

def main():
    # 使用config.py中定义的端口，或者一个默认值
    port = getattr(config, 'MARKET_TRADE_PORT', 5003)
    
    # 定义服务器的“名片”
    agent_card = AgentCard(
        name="Market Trade A2A Agent",
        description="Handles cross-border payment bridging, blockchain operations, and other complex tasks.",
        url=f"http://localhost:{port}",
        skills=[
            AgentSkill(name="process_payment", description="Handles course purchase and payment flows."),
            AgentSkill(name="operate_blockchain", description="Performs queries and transactions on the IoTeX testnet."),
            AgentSkill(name="create_story", description="Generates creative stories based on prompts.")
        ]
    )
    
    # 创建并启动服务器
    server = MarketTradeServer(agent_card)
    
    print("\n" + "="*60)
    print("🚀 Starting Market Trade A2A Server...")
    print(f"👂 Listening on http://localhost:{port}")
    print("   This server provides all trading, payment, and blockchain functionalities.")
    print("="*60)
    
    run_server(server, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()