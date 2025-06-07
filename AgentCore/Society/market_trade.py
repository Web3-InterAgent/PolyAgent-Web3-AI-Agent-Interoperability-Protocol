from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from eth_account import Account
from string import Template

import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from AgentCore.Tools.iotextoken_toolkit import IotexTokenToolkit
from camel.toolkits import MCPToolkit
from camel.societies import RolePlaying
from AgentCore.config import config

from camel.types import (
    ModelPlatformType,
    ModelType,
    OpenAIBackendRole,
    RoleType,
    TaskType,
)

class AgentManager:
    def __init__(self):
        self.estnet_rpc = "https://babel-api.testnet.iotex.io"
        self.chain_id = 4690

        self.ERC20_ABI = [
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_from", "type": "address"},
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transferFrom",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]

        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.MODELSCOPE,
            model_type='Qwen/Qwen2.5-72B-Instruct',
            model_config_dict={'temperature': 0.2},
            api_key='9d3aed4d-eca1-4e0c-9805-cb923ccbbf21',
        )

        self.iotex_agent = ChatAgent(
            system_message="""
            你是一个 IoTeX 测试网专用的区块链助手 Agent，具备以下功能：

            =================
            ✅ 支持的查询功能
            =================
            1. 查询账户 IOTX 主币余额  
            - 函数: iotex_balance  
            - 参数: wallet_address

            2. 查询账户 ERC20 代币余额  
            - 函数: erc20_balance  
            - 参数: wallet_address, token_contract_address

            3. 查询 ERC20 授权额度（allowance）  
            - 函数: erc20_allowance  
            - 参数: owner_address, spender_address, token_contract_address, [decimals]（可选）

            4. 查询 ERC20 代币合约信息  
            - 函数: erc20_contract_info  
            - 参数: token_contract_address

            =================
            🛠️ 支持的交易功能
            =================
            5. 授权 ERC20 代币使用（approve）  
            - 函数: erc20_approve  
            - 参数: private_key, spender_address, token_contract_address, amount, [decimals]（可选）

            6. 执行 ERC20 代币的 transferFrom 转账  
            - 函数: erc20_transfer_from  
            - 参数: private_key, token_contract_address, from_address, to_address, amount, [decimals]（可选）

            =================
            💬 交互与提醒
            💬 交互与提醒
            =================
            - 查询类操作需提供相关地址，若涉及 ERC20，需包含合约地址。
            - 所有链上写入操作必须先确认，方可执行。
            - 若涉及私钥（如交易类操作），必须提醒用户注意安全，**不建议明文传播私钥**，应使用环境变量或签名工具传递。
            - 所有操作仅限 IoTeX 测试网。

            =======================
            📦 已知默认用户参数
            =======================
            - 查询类操作需提供相关地址，若涉及 ERC20，需包含合约地址。
            - 所有链上写入操作必须先确认，方可执行。
            - 若涉及私钥（如交易类操作），必须提醒用户注意安全，**不建议明文传播私钥**，应使用环境变量或签名工具传递。
            - 所有操作仅限 IoTeX 测试网。

            =======================
            📦 已知默认用户参数
            =======================
            # PolyAgent Token 合约地址（ERC20）
            polyagent_token_contract = "0xD3286E20Ff71438D9f6969828F7218af4A375e2f"

            # 发送者账户信息
            Sender Address: "0xE4949a0339320cE9ec93c9d0836c260F23DFE8Ca"
            Sender Private Key: "e4ad52fbc8c6fe3f4069af70363b24ca4453dbf472d92f83a8adf38e8010991f"


            # 授权者（Spender）账户信息

            Spender Address: "0xf874871Bc0f99a06b5327F34AceAa80Ae71905DE"
            Spender Private Key: "3efe78303dcf8ea3355ef363f04eb442e000081fe66ebcebf5d9cf19f3ace8b8"
            # 默认精度和授权数量
            decimals = 18
            amount = 2



            =======================
            =======================
            🤖 调用行为规则[十分重要]
            =======================
            你已拥有所有所需参数，默认以上述信息填充。当用户发起查询或交易请求时，请根据内容直接选择合适的函数并执行。除非用户明确指定覆盖默认值，否则无需再次请求参数。
            
            """,
            model=self.model,
            token_limit=32768,
            tools=[*IotexTokenToolkit(self.estnet_rpc, self.ERC20_ABI, self.chain_id).get_tools()],
            output_language="en"
        )

        self.story_agent = ChatAgent(
            system_message="""    
            [系统提示]你已收到5个XRC20代币作为奖励。

            请根据以下用户的需求，创作一段风格化的微型故事。请确保故事开头就体现这一事件："收到5个XRC20代币"。

            风格可以是奇幻、科幻、悬疑、童话或赛博朋克等任选其一。

            用户的需求是：$user_demand

            要求：
            - 故事开头应明确提到"收到5个XRC20代币"
            - 故事应围绕这个需求展开，体现其意义或引发的事件
            - 文风有代入感，故事背景清晰，人物设定简洁有力
            - 不需要分段，字数在150字左右
            - 结尾应带有开放性或暗示更大背景的发展

            请开始生成故事。""",
            model=self.model,
            token_limit=32768,
            output_language="en"
        )

        # 添加演示流程状态跟踪
        self.demo_step = 0
        self.demo_context = {
            "order_id": "ORDER20250106001",
            "amount_usd": 15,
            "amount_tokens": 15,
            "merchant_wallet": "0xf874871Bc0f99a06b5327F34AceAa80Ae71905DE",
            "user_wallet": "0xE4949a0339320cE9ec93c9d0836c260F23DFE8Ca",
            "usd_to_rmb_rate": 7.25,  # USD to RMB exchange rate
            "download_link": "http://localhost:5000/download/premium_service_guide.txt" # 修改为downloads文件夹中的txt文件
        }

    async def smart_route_request(self, user_input: str):
        """
        智能路由用户请求到合适的Agent
        根据演示流程和关键词自动选择处理方式
        """
        user_input_lower = user_input.lower()
        
        # Step 1: 创建支付订单 - 修改为匹配alipay关键词
        if any(keyword in user_input_lower for keyword in ["alipay", "purchase", "buy", "order", "service", "$"]):
            self.demo_step = 1
            return await self.handle_step1_create_order(user_input)
            
        # Step 2: 用户获得代币授权 (原Step 3)
        elif any(keyword in user_input_lower for keyword in ["authorize", "approve tokens"]):
            if self.demo_step >= 1: # 必须在创建订单后才能授权
                self.demo_step = 2
                return await self.handle_step2_token_authorization(user_input)
            else:
                return "Please create an order first by typing 'purchase'."
            
        # Step 3: 转账给商家 (原Step 4)
        elif any(keyword in user_input_lower for keyword in ["transfer", "send tokens"]):
            if self.demo_step >= 2:
                self.demo_step = 3
                return await self.handle_step3_token_transfer(user_input)
            else:
                return "Please authorize the token transfer first by typing 'Authorize tokens'."

        # Step 4: PayPal收款转换 (原Step 5)
        elif any(keyword in user_input_lower for keyword in ["convert", "paypal"]):
            if self.demo_step >= 3:
                self.demo_step = 4
                return await self.handle_step4_paypal_conversion(user_input)
            else:
                return "Please transfer the tokens first by typing 'Transfer tokens'."
            
        # Step 5: 服务交付 (原Step 6)
        elif any(keyword in user_input_lower for keyword in ["delivery", "download", "get guide"]):
            if self.demo_step >= 4:
                self.demo_step = 5
                return await self.handle_step5_service_delivery(user_input)
            else:
                return "Please complete the PayPal conversion step first."
            
        # 默认支付宝查询
        elif any(keyword in user_input_lower for keyword in ["query", "status", "check"]):
            return await self.run_alipay_query("query order status")
            
        else:
            # 其他请求路由到IoTeX agent
            response = self.iotex_agent.step(user_input)
            return response.msgs[0].content if response and response.msgs else "Unable to process your request"

    async def handle_step1_create_order(self, user_input: str):
        """
        第一步：创建支付宝支付订单 - 先返回连接状态，再处理订单
        """
        print(f"(Order Creation) for user: {user_input}")

        # 计算人民币金额
        amount_rmb = self.demo_context['amount_usd'] * self.demo_context['usd_to_rmb_rate']
        
        # 调用支付宝MCP服务
        payment_info = await self.run_alipay_query(
            f"Create a payment order for {amount_rmb:.2f} RMB to purchase a $15.00 USD product, with order ID {self.demo_context['order_id']}"
        )
        
        # 返回完整的支付信息
        return f"""
<div class="demo-step-indicator">
    <span class="step-number">1/5</span> Initializing Cross-Border Payment
</div>
<div class="payment-info-card" style="background-color: #2a2a2a; border: 1px solid #444; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
    <h3 style="color: #EAEAEA; border-bottom: 1px solid #444; padding-bottom: 10px;">Premium Web3 Payment Guide</h3>
    <div style="background: rgba(74, 144, 226, 0.1); border-left: 3px solid #4A90E2; padding: 10px; margin: 15px 0; font-size: 0.9em; color: #94A3B8;">
        You're using PolyAgent's cross-border payment bridge to buy an international product with Alipay.
    </div>
    <div class="info-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
        <div><strong style="color: #BDBDBD;">Product Price:</strong><br><span style="color: #FFFFFF;">${self.demo_context['amount_usd']:.2f} USD</span></div>
        <div><strong style="color: #BDBDBD;">Order ID:</strong><br><span style="color: #FFFFFF; font-family: 'Courier New', Courier, monospace;">{self.demo_context['order_id']}</span></div>
        <div><strong style="color: #BDBDBD;">Exchange Rate:</strong><br><span style="color: #FFFFFF;">1 USD ≈ {self.demo_context['usd_to_rmb_rate']} RMB</span></div>
        <div><strong style="color: #BDBDBD;">Estimated Total:</strong><br><span style="color: #FFFFFF; font-weight: bold;">¥{amount_rmb:.2f} RMB</span></div>
    </div>
</div>

{payment_info}
"""

    async def handle_step2_token_authorization(self, user_input: str):
        """
        第二步：用户授权代币 (原Step 3)
        """
        print(f"(Authorization) for user: {user_input}")
        response = await self.iotex_agent.astep(
            "Please approve 15 PolyAgent tokens for the spender to bridge the payment."
        )
        
        content = response.msgs[0].content if response and response.msgs else "Authorization failed."
        
        return f"""
<div class="demo-step-indicator">
    <span class="step-number">2/5</span> Bridge Authorization
</div>
<div class="response-container">
    {content}
</div>
<div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>✅ Token authorization successful.</strong><br>
    This allows us to use the IoTeX blockchain to securely convert your payment. Next, type "<strong>Transfer tokens</strong>".
</div>
"""

    async def handle_step3_token_transfer(self, user_input: str):
        """
        第三步：转账给商家 (原Step 4)
        """
        print(f"(Transfer) for user: {user_input}")
        response = await self.iotex_agent.astep(
            f"Transfer 15 PolyAgent tokens from my wallet to the merchant wallet {self.demo_context['merchant_wallet']} to complete the bridge transaction."
        )
        
        content = response.msgs[0].content if response and response.msgs else "Transfer failed."
        
        return f"""
<div class="demo-step-indicator">
    <span class="step-number">3/5</span> Cross-Chain Transfer
</div>
<div class="response-container">
    {content}
</div>
<div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>✅ Funds transferred via blockchain bridge.</strong><br>
    We are now converting the funds to be delivered to the merchant. Next, type "<strong>Convert with PayPal</strong>".
</div>
"""

    async def handle_step4_paypal_conversion(self, user_input: str):
        """
        第四步：PayPal收款转换 (原Step 5)
        """
        print(f"(PayPal) for user: {user_input}")
        response = await self.run_paypal_query(
            "The customer's payment has been bridged. Create an invoice to receive $15.00 USD in the merchant's PayPal account."
        )
        
        return f"""
<div class="demo-step-indicator">
    <span class="step-number">4/5</span> Final Currency Conversion
</div>
<div class="response-container">
    {response}
</div>
<div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>✅ Success! Payment delivered in USD.</strong><br>
    The merchant has received $15.00 USD in their PayPal account. Next, type "<strong>Get guide</strong>" to download your purchase.
</div>
"""

    async def handle_step5_service_delivery(self, user_input: str):
        """
        第五步：服务交付 - 提供下载链接 (原Step 6)
        """
        print(f"(Delivery) for user: {user_input}")
        download_link = self.demo_context.get("download_link", "#")
        
        return f"""
<div class="demo-step-indicator">
    <span class="step-number">5/5</span> Service Delivery
</div>

<div class="premium-download-container">
    <div class="success-checkmark">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M9 12L11 14L15 10" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
    </div>
    
    <h3 class="download-title">🎉 Purchase Complete!</h3>
    <p class="download-subtitle">Your Premium Web3 Payment Guide is ready for download.</p>
    
    <a href="{download_link}" style="color: white; text-decoration: underline; font-size: 24px; display: block; text-align: center; margin: 20px 0;" target="_blank">
        download your file
    </a>
    
    <div class="download-info">
        <strong>📋 What's included:</strong><br>
        • Complete Web3 payment integration guide<br>
        • Cross-border payment bridge architecture<br>
        • Real-world implementation examples<br>
        • Security best practices and troubleshooting
    </div>
    
    <div class="download-stats">
        <div class="stat-item">
            <span>📄</span>
            <span>72 pages</span>
        </div>
        <div class="stat-item">
            <span>⚡</span>
            <span>Instant access</span>
        </div>
        <div class="stat-item">
            <span>🔄</span>
            <span>Free updates</span>
        </div>
    </div>
</div>

<div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 8px; padding: 16px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>✨ Cross-Border Payment Complete!</strong><br>
    Your payment journey: <strong>Alipay (CNY)</strong> → <strong>IoTeX (USDT)</strong> → <strong>PayPal (USD)</strong> was successful.<br>
    <span style="color: #00D084;">Transaction ID: TXN-{self.demo_context['order_id']}-{hash(user_input) % 10000:04d}</span>
</div>
"""

    async def run_alipay_query(self, query: str):
        import os
                # 使用绝对路径来定位 MCP 配置文件，避免相对路径问题
        config_path = os.path.join(os.path.dirname(__file__), "..", "Mcp", "alipay_server.json")
        config_path = os.path.abspath(config_path)
        
        try:
            async with MCPToolkit(config_path=config_path) as mcp_toolkit:
                alipay_agent = ChatAgent(
                    system_message="""
                    You are an Alipay Agent for a cross-border payment service. Your task is to create a payment order in Chinese Yuan (RMB) for a product priced in US Dollars.

                    **Action: Create Payment Order (`create_payment`)**
                    - When a user wants to pay, call the `create_payment` function.
                    - Use these exact parameters:
                        - `outTradeNo`: 'ORDER20250106001'
                        - `totalAmount`: '108.75'  (This is the RMB equivalent of $15.00 USD)
                        - `orderTitle`: 'PolyAgent Service - Intl. Purchase'

                    **Response Format:**
                    - You MUST return an HTML block with a payment link. Use this exact format:
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="[支付链接]" class="alipay-payment-button" target="_blank" onclick="handleAlipayPayment(this)">Confirm Payment with Alipay</a>
                    </div>
                    
                    <div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
                        <strong>💡 Payment Instructions:</strong><br>
                        1. Click the button to open the Alipay payment page.<br>
                        2. After completing the payment, type "<strong>Authorize tokens</strong>" in the chat to continue the cross-border process.
                    </div>
                    """,
                    model=self.model,
                    token_limit=32768,
                    tools=[*mcp_toolkit.get_tools()],
                    output_language="en"
                )

                response = await alipay_agent.astep(query)
                
                if response and response.msgs:
                    return response.msgs[0].content
                else:
                    return "Unable to get Alipay response"
                    
        except Exception as e:
            error_msg = f"支付宝处理过程中出现错误: {str(e)}"
            print(error_msg)
            return f"""❌ Alipay Processing Error

An error occurred while processing Alipay request: {str(e)}
Please check Alipay MCP server status and try again."""

    async def run_paypal_query(self, query: str):
        import os
        # 使用绝对路径来定位 PayPal MCP 配置文件，避免相对路径问题
        config_path = os.path.join(os.path.dirname(__file__), "..", "Mcp", "paypal_server.json")
        config_path = os.path.abspath(config_path)
        
        try:
            async with MCPToolkit(config_path=config_path) as mcp_toolkit:
                paypal_agent = ChatAgent(
                    system_message="""
                      你是一个经验丰富的 Paypal 交易代理，负责协助用户完成以下操作：

                1. 创建发票（create_invoice）
                2. 查询订单状态（query_order）
                3. 处理退款请求（process_refund）

                请根据用户的具体需求使用合适的工具进行操作，确保金额、税费、折扣等计算准确，语言清晰专业。
                    """,
                    model=self.model,
                    token_limit=32768,
                    tools=[*mcp_toolkit.get_tools()],
                    output_language="en"
                )

                response = await paypal_agent.astep(query)
                
                if response and response.msgs:
                    return response.msgs[0].content
                else:
                    return "Unable to get PayPal response"
                    
        except Exception as e:
            error_msg = f"PayPal处理过程中出现错误: {str(e)}"
            print(error_msg)
            return f"""❌ PayPal Processing Error

An error occurred while processing PayPal request: {str(e)}
Please check PayPal MCP server status and try again."""

    async def run_amap_query(self, query: str):
        config_path = "E:\\EnjoyAI\\Web3-Agent-Protocal\\workspace_new\\AgentCore\\Mcp\\amap_server.json"

        async with MCPToolkit(config_path=config_path) as mcp_toolkit:
            amap_agent = ChatAgent(
                system_message="""
                你是一个高德地图骑行助手，擅长分析用户的出行需求，并基于实时数据、路线安全性、景色美观度和道路类型，为用户推荐最优骑行路线。

                请根据用户的出发地、目的地，以及是否偏好快速到达、风景优美或避开车流等偏好，推荐一条骑行路线。

                你需要：
                1. 指出推荐的路线途经哪些关键路段或地标。
                2. 说明这条路线在时间、距离、风景、安全性等方面的优势。
                3. 简洁明了地解释为何这是当前最优选择。

                请以自然语言中文回答，条理清晰，重点突出。
                """,
                model=self.model,
                token_limit=32768,
                tools=[*mcp_toolkit.get_tools()],
                output_language="en"
            )

            response = await amap_agent.astep(query)
            print("Agent response：\n", response.msgs[0].content)

    async def run_all(self):
        """执行完整的支付流程演示"""
        results = []
        
        # 步骤1: 创建支付订单
        print("📱 步骤1: 创建支付宝支付订单...")
        payment_result = await self.run_alipay_query("支付")
        results.append(f"步骤1 - 支付订单创建:\n{payment_result}")
        
        # 步骤2: 查询支付状态  
        print("\n📊 步骤2: 查询支付状态...")
        query_result = await self.run_alipay_query("查询订单")
        results.append(f"步骤2 - 支付状态查询:\n{query_result}")
        
        # 步骤3: 查询授权额度
        print("\n🔍 步骤3: 查询ERC20代币授权额度...")
        allowance_response = self.iotex_agent.step("帮我查询一下ERC20代币的授权额度。")
        allowance_result = allowance_response.msgs[0].content if allowance_response and allowance_response.msgs else "查询失败"
        results.append(f"步骤3 - 授权额度查询:\n{allowance_result}")
        
        # 步骤4: 执行代币授权
        print("\n🔐 步骤4: 执行代币授权操作...")
        approve_response = self.iotex_agent.step("我想给0xf874871Bc0f99a06b5327F34AceAa80Ae71905DE地址授权200个代币，请帮我执行该操作")
        approve_result = approve_response.msgs[0].content if approve_response and approve_response.msgs else "授权失败"
        results.append(f"步骤4 - 代币授权:\n{approve_result}")
        
        # 步骤5: 执行稳定币转账
        print("\n💸 步骤5: 执行稳定币转账...")
        transfer_response = self.iotex_agent.step("我想给0xf874871Bc0f99a06b5327F34AceAa80Ae71905DE地址转账5个代币，请帮我执行该操作")
        transfer_result = transfer_response.msgs[0].content if transfer_response and transfer_response.msgs else "转账失败"
        results.append(f"步骤5 - 稳定币转账:\n{transfer_result}")
        
        # 步骤6: 提供定制故事服务
        print("\n📖 步骤6: 生成定制故事服务...")
        story_response = self.story_agent.step("我希望写一个勇士拯救公主的故事")
        story_result = story_response.msgs[0].content if story_response and story_response.msgs else "故事生成失败"
        results.append(f"步骤6 - 故事服务交付:\n{story_result}")
        
        return results


if __name__ == "__main__":
    agent_manager = AgentManager()
    agent_manager = AgentManager()
    asyncio.run(agent_manager.run_all())
