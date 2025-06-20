import {
	faCommentAlt,
	faMicrophone,
	faPaperPlane,
	// faUser,
	faPlus,
	faTimes,
	faSignature,
	faPen,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useEffect, useRef, useState } from "react";

// RainbowKit 相关导入
import "@rainbow-me/rainbowkit/styles.css";

// 添加自定义样式
import "./ai-response.css";
import "./rainbow.css";

// Stagewise will be dynamically imported in the App component

import {
	ConnectButton,
	getDefaultConfig,
	RainbowKitProvider,
} from "@rainbow-me/rainbowkit";
import {
	WagmiProvider,
	useAccount,
	useSignMessage,
	useBalance,
	useSendTransaction,
} from "wagmi";
import { mainnet, polygon, optimism, arbitrum, base } from "wagmi/chains";
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { http } from "wagmi";
import { parseEther } from "viem";
import type { Chain } from "wagmi/chains";

// 定义 IoTeX 测试网络
const iotexTestnet: Chain = {
  id: 4690,
  name: "IoTeX Testnet",
  nativeCurrency: {
    name: "IoTeX",
    symbol: "IOTX",
    decimals: 18,
  },
  rpcUrls: {
    default: {
      http: ["https://babel-api.testnet.iotex.one"],
    },
  },
  blockExplorers: {
    default: {
      name: "IoTeX Testnet Explorer",
      url: "https://testnet.iotexscan.io",
    },
  },
  contracts: {},
  testnet: true,
};


// 配置 RainbowKit
const config = getDefaultConfig({
	appName: "InterAgent",
	// 从 WalletConnect Cloud 获取项目ID: https://cloud.walletconnect.com/
	// 1. 注册/登录 WalletConnect Cloud
	// 2. 创建一个新项目并输入应用名称和URL
	// 3. 复制生成的项目ID到这里
  // projectId: "d56e1374c9d4380694fc205749b5eec2",
	projectId: atob("ZDU2ZTEzNzRjOWQ0MzgwNjk0ZmMyMDU3NDliNWVlYzI="),
	chains: [mainnet, polygon, optimism, arbitrum, base, iotexTestnet],
	transports: {
		// [mainnet.id]: http("https://eth-mainnet.g.alchemy.com/v2/demo"),
		// [polygon.id]: http("https://polygon-mainnet.g.alchemy.com/v2/demo"),
		// [optimism.id]: http("https://opt-mainnet.g.alchemy.com/v2/demo"),
		// [arbitrum.id]: http("https://arb-mainnet.g.alchemy.com/v2/demo"),
		// [base.id]: http("https://base-mainnet.g.alchemy.com/v2/demo"),
    [iotexTestnet.id]: http("https://babel-api.testnet.iotex.one"),
	},
	ssr: true,
});

const queryClient = new QueryClient();

interface Message {
	text: string;
	sender: "user" | "ai";
	type?: "html" | "text";
}

interface Conversation {
	id: string;
	title: string;
	messages: Message[];
	createdAt: number;
}



// 添加AI助手类型枚举
type AIAgentType = "shopping" | "trade";

// 签名功能组件
function WalletSignature() {
  const { address, isConnected, chain } = useAccount();
  const { data: balance } = useBalance({ address });
  const [messageToSign, setMessageToSign] = useState("");
  const [signatureResult, setSignatureResult] = useState("");
  const [recipientAddress, setRecipientAddress] = useState("");
  const [sendAmount, setSendAmount] = useState("");
  // const [showSignaturePanel, setShowSignaturePanel] = useState(false);
  const { signMessage, isPending: isSignPending } = useSignMessage({
    mutation: {
      onSuccess: (signature) => {
        setSignatureResult(signature);
        console.log("签名成功:", signature);
      },
      onError: (error) => {
        console.error("签名失败:", error);
        setSignatureResult(`签名失败: ${error.message}`);
      },
    },
  });

  const { sendTransaction, isPending: isSendPending } = useSendTransaction({
    mutation: {
      onSuccess: (hash) => {
        console.log("交易发送成功:", hash);
        alert(`交易发送成功! 哈希: ${hash}`);
      },
      onError: (error) => {
        console.error("交易发送失败:", error);
        alert(`交易发送失败: ${error.message}`);
      },
    },
  });

  const handleSignMessage = () => {
    if (!messageToSign.trim()) {
      alert("Please enter a message to sign");
      return;
    }
    signMessage({ message: messageToSign });
  };

  const handleSendTransaction = () => {
    if (!recipientAddress.trim() || !sendAmount.trim()) {
      alert("Please fill in recipient address and amount");
      return;
    }

    try {
      sendTransaction({
        to: recipientAddress as `0x${string}`,
        value: parseEther(sendAmount),
      });
    } catch (error) {
      console.error("交易参数错误:", error);
      alert("Transaction parameter error, please check address and amount format");
    }
  };

  if (!isConnected) {
    return (
      <div className="wallet-signature-panel p-4 bg-deep-black/50 backdrop-blur-sm rounded-lg border border-night-purple/20">
        <p className="text-text-secondary text-center">
          Please connect your wallet to use signature features
        </p>
      </div>
    );
  }

  return (
    <div className="wallet-signature-panel p-4 bg-deep-black/50 backdrop-blur-sm rounded-lg border border-night-purple/20 space-y-4">
      {/* 钱包信息 */}
      <div className="wallet-info border-b border-night-purple/20 pb-4">
        <h3 className="text-neon-cyan font-bold mb-2 flex items-center">
          <FontAwesomeIcon icon={faSignature} className="mr-2" />
          Wallet Signature Tools
        </h3>
        <div className="text-sm space-y-1">
          {/* <p><span className="text-text-secondary">地址:</span> <span className="text-neon-cyan font-mono">{address}</span></p> */}
          <p>
            <span className="text-text-secondary">Network:</span>{" "}
            <span className="text-neon-cyan">{chain?.name}</span>
          </p>
          <p>
            <span className="text-text-secondary">Balance:</span>{" "}
            <span className="text-neon-cyan">
              {balance
                ? `${parseFloat(balance.formatted).toFixed(4)} ${
                    balance.symbol
                  }`
                : "Loading..."}
            </span>
          </p>
        </div>
      </div>

      {/* 消息签名 */}
      <div className="message-signing">
        <h4 className="text-text-primary font-semibold mb-2 flex items-center">
          <FontAwesomeIcon icon={faPen} className="mr-2 text-xs" />
          Message Signing
        </h4>
        <div className="space-y-2">
          <textarea
            placeholder="Enter message to sign..."
            className="w-full p-2 bg-deep-black border border-night-purple/30 rounded text-text-primary placeholder-text-secondary resize-none"
            rows={2}
            value={messageToSign}
            onChange={(e) => setMessageToSign(e.target.value)}
          />
          <button
            onClick={handleSignMessage}
            disabled={isSignPending}
            className="w-full px-4 py-2 bg-gradient-to-r from-neon-cyan/20 to-night-purple/20 hover:from-neon-cyan/30 hover:to-night-purple/30 border border-neon-cyan/30 text-neon-cyan rounded transition-all disabled:opacity-50"
          >
            {isSignPending ? "Signing..." : "Sign Message"}
          </button>
          {signatureResult && (
            <div className="signature-result p-2 bg-deep-black/80 border border-neon-cyan/20 rounded">
              <p className="text-xs text-text-secondary mb-1">Signature Result:</p>
              <p className="text-xs text-neon-cyan font-mono break-all">
                {signatureResult}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 发送交易 */}
      <div className="send-transaction">
        <h4 className="text-text-primary font-semibold mb-2">Send Transaction</h4>
        <div className="space-y-2">
                      <input
              type="text"
              placeholder="Recipient Address (0x...)"
              className="w-full p-2 bg-deep-black border border-night-purple/30 rounded text-text-primary placeholder-text-secondary"
              value={recipientAddress}
              onChange={(e) => setRecipientAddress(e.target.value)}
            />
            <input
              type="number"
              placeholder="Amount"
              step="0.001"
              className="w-full p-2 bg-deep-black border border-night-purple/30 rounded text-text-primary placeholder-text-secondary"
              value={sendAmount}
              onChange={(e) => setSendAmount(e.target.value)}
            />
          <button
            onClick={handleSendTransaction}
            disabled={isSendPending}
            className="w-full px-4 py-2 bg-gradient-to-r from-night-purple/20 to-neon-cyan/20 hover:from-night-purple/30 hover:to-neon-cyan/30 border border-night-purple/30 text-text-primary rounded transition-all disabled:opacity-50"
          >
            {isSendPending
              ? "Sending..."
              : `Send ${chain?.nativeCurrency.symbol || "Stablecoin"}`}
          </button>
        </div>
      </div>
    </div>
  );
}

function App() {
	const [messages, setMessages] = useState<Message[]>([]);
	const [inputMessage, setInputMessage] = useState("");
	const chatContainerRef = useRef<HTMLDivElement>(null);
	const [isTyping, setIsTyping] = useState(false);
	const textareaRef = useRef<HTMLTextAreaElement>(null);
	const [conversations, setConversations] = useState<Conversation[]>([]);
	const [currentConversationId, setCurrentConversationId] = useState<
		string | null
	>(null);

	const [showLogoOverlay, setShowLogoOverlay] = useState(false);

	// Stagewise toolbar state (development only)
	const [StagewiseToolbar, setStagewiseToolbar] = useState<any>(null);
	const [ReactPlugin, setReactPlugin] = useState<any>(null);

	// Load stagewise components dynamically in development mode
	useEffect(() => {
		if (import.meta.env.DEV) {
			const loadStagewise = async () => {
				try {
					const [toolbarModule, pluginModule] = await Promise.all([
						import('@stagewise/toolbar-react'),
						import('@stagewise-plugins/react')
					]);
					
					setStagewiseToolbar(() => toolbarModule.StagewiseToolbar);
					setReactPlugin(() => pluginModule.ReactPlugin);
					console.log('✅ Stagewise toolbar loaded successfully');
				} catch (error) {
					console.warn('🔧 Stagewise toolbar not available (install with: pnpm add @stagewise/toolbar-react @stagewise-plugins/react --save-dev)');
				}
			};
			
			loadStagewise();
		}
	}, []);

	// 添加AI助手选择状态
	const [selectedAgent, setSelectedAgent] = useState<AIAgentType>("shopping");
	const [isAgentSwitching, setIsAgentSwitching] = useState(false);

	// Tooltip状态
	const [showTooltip, setShowTooltip] = useState<{
		show: boolean;
		agent: AIAgentType | null;
		position: { x: number; y: number };
	}>({
		show: false,
		agent: null,
		position: { x: 0, y: 0 }
	});

	// AI助手切换处理函数
	const handleAgentSwitch = async (agentType: AIAgentType) => {
		if (agentType === selectedAgent || isAgentSwitching) return;

		setIsAgentSwitching(true);

		// 模拟切换动画延迟
		await new Promise(resolve => setTimeout(resolve, 300));

		setSelectedAgent(agentType);
		setIsAgentSwitching(false);

		console.log(`AI助手已切换至: ${agentType === 'shopping' ? '百度优选购物' : '支付宝转stablecoin'}`);
	};

	// Tooltip处理函数
	const handleMouseEnter = (agent: AIAgentType, event: React.MouseEvent) => {
		const rect = event.currentTarget.getBoundingClientRect();
		setShowTooltip({
			show: true,
			agent,
			position: {
				x: rect.left + rect.width / 2,
				y: rect.bottom + 8
			}
		});
	};

	const handleMouseLeave = () => {
		setShowTooltip({
			show: false,
			agent: null,
			position: { x: 0, y: 0 }
		});
	};

	// 获取Agent描述信息
	const getAgentDescription = (agent: AIAgentType) => {
		if (agent === "shopping") {
			return {
				title: "🛍️ 百度优选购物助手",
				description: "智能商品搜索、参数对比、品牌排行和在线购买服务",
				features: [
					"🔍 商品搜索与推荐",
					"📊 商品参数对比分析", 
					"🏆 品牌排行榜查询",
					"🛒 在线购买与订单管理",
					"🔧 售后服务支持"
				]
			};
		} else {
			return {
				title: "💰 Payment Bridge Assistant",
				description: "Assist with stablecoin transfers and cross-border payment operations",
				features: [
					"💳 跨境支付桥接",
					"🔗 区块链代币操作",
					"📝 智能合约交互",
					"📊 交易状态追踪"
				]
			};
		}
	};
  const [showSignaturePanel, setShowSignaturePanel] = useState(false);

	// 从本地存储加载对话
	useEffect(() => {
		const storedConversations = localStorage.getItem("poly-ai-conversations");
		if (storedConversations) {
			setConversations(JSON.parse(storedConversations));
		}

		const currentId = localStorage.getItem("poly-ai-current-conversation");
		if (currentId) {
			setCurrentConversationId(currentId);
			const currentConversation = JSON.parse(storedConversations || "[]").find(
				(conv: Conversation) => conv.id === currentId
			);
			if (currentConversation) {
				setMessages(currentConversation.messages);
			}
		}
	}, []);

	// 保存对话到本地存储
	useEffect(() => {
		if (conversations.length > 0) {
			localStorage.setItem(
				"poly-ai-conversations",
				JSON.stringify(conversations)
			);
		}

		if (currentConversationId) {
			localStorage.setItem(
				"poly-ai-current-conversation",
				currentConversationId
			);

			// 更新当前对话的消息
			const updatedConversations = conversations.map((conv) =>
				conv.id === currentConversationId ? { ...conv, messages } : conv
			);

			setConversations(updatedConversations);
			localStorage.setItem(
				"poly-ai-conversations",
				JSON.stringify(updatedConversations)
			);
		}
	}, [messages, currentConversationId]);

	// 创建粒子效果
	useEffect(() => {
		const particles = document.getElementById("particles");
		const particleCount = 30;

		if (particles) {
			for (let i = 0; i < particleCount; i++) {
				const particle = document.createElement("div");
				particle.classList.add("particle");

				// 随机位置
				particle.style.left = `${Math.random() * 100}%`;
				particle.style.top = `${Math.random() * 100}%`;

				// 随机大小
				const size = Math.random() * 3 + 1;
				particle.style.width = `${size}px`;
				particle.style.height = `${size}px`;

				// 随机透明度
				particle.style.opacity = `${Math.random() * 0.5 + 0.1}`;

				// 动画
				particle.style.animationName = "float";
				particle.style.animationDuration = `${Math.random() * 10 + 5}s`;
				particle.style.animationDelay = `${Math.random() * 5}s`;

				particles.appendChild(particle);
			}
		}
	}, []);

	// 创建新对话
	const createNewConversation = () => {
		console.log("创建新对话被调用");
		console.trace("调用堆栈");

		const newId = `conv-${Date.now()}`;
		const newConversation: Conversation = {
			id: newId,
			// title: `new Chat ${conversations.length + 1}`,
			title: `new Chat`,
			messages: [],
			createdAt: Date.now(),
		};

		setConversations((prev) => [newConversation, ...prev]);
		setCurrentConversationId(newId);
		setMessages([]);

		console.log("新对话创建完成，ID:", newId);
	};

	// 选择对话
	const selectConversation = (id: string) => {
		const conversation = conversations.find((conv) => conv.id === id);
		if (conversation) {
			setCurrentConversationId(id);
			setMessages(conversation.messages);
		}
	};

	// 删除对话
	const deleteConversation = (conversationId: string, e: React.MouseEvent) => {
		e.stopPropagation(); // 阻止事件冒泡，避免触发选择对话

		// 如果删除的是当前激活的对话
		if (conversationId === currentConversationId) {
			// 找到剩余对话中的第一个作为新的激活对话
			const remainingConversations = conversations.filter(conv => conv.id !== conversationId);

			if (remainingConversations.length > 0) {
				// 选择第一个剩余对话
				const firstRemaining = remainingConversations[0];
				setCurrentConversationId(firstRemaining.id);
				setMessages(firstRemaining.messages);
			} else {
				// 没有剩余对话，创建新对话
				createNewConversation();
			}
		}

		// 从对话列表中移除
		const updatedConversations = conversations.filter(conv => conv.id !== conversationId);
		setConversations(updatedConversations);

		// 更新localStorage
		localStorage.setItem("poly-ai-conversations", JSON.stringify(updatedConversations));

		// 如果删除的是当前对话且没有其他对话，清除当前对话ID
		if (conversationId === currentConversationId && updatedConversations.length === 0) {
			localStorage.removeItem("poly-ai-current-conversation");
		}
	};

	// 课程信息提取函数
	const extractCourseInfo = (userInput: string) => {
		if (userInput.toLowerCase().includes("python")) {
			return {
				name: "Primary Python Course",
				platform: "edX",
				duration: "8 weeks",
				level: "Beginner to Intermediate",
				description: "Learn Python programming fundamentals through hands-on exercises and projects. This comprehensive course covers Python syntax, data structures, functions, and object-oriented programming concepts essential for modern development.",
				price_usd: 49.99,
				price_rmb: 49.99 * 7.25,
				order_id: "ORDER20250107001",
				preview_url: "https://www.edx.org/learn/python",
				instructor: "edX Professional Education",
				certificate: "Verified Certificate Available"
			};
		} else if (userInput.toLowerCase().includes("web") || userInput.toLowerCase().includes("javascript")) {
			return {
				name: "Full Stack Web Development Bootcamp",
				platform: "edX",
				duration: "12 weeks",
				level: "Intermediate to Advanced",
				description: "Learn to build complete web applications using modern technologies like React, Node.js, and MongoDB. Includes deployment and DevOps practices.",
				price_usd: 89.99,
				price_rmb: 89.99 * 7.25,
				order_id: "ORDER20250107002",
				preview_url: "https://www.edx.org/learn/web-development",
				instructor: "edX Professional Education",
				certificate: "Professional Certificate"
			};
		} else {
			return {
				name: "AI & Machine Learning Fundamentals",
				platform: "edX",
				duration: "10 weeks",
				level: "Beginner to Intermediate",
				description: "Explore the fundamentals of artificial intelligence and machine learning. Learn to build and deploy ML models using Python, TensorFlow, and scikit-learn.",
				price_usd: 69.99,
				price_rmb: 69.99 * 7.25,
				order_id: "ORDER20250107003",
				preview_url: "https://www.edx.org/learn/artificial-intelligence",
				instructor: "edX Professional Education",
				certificate: "Professional Certificate"
			};
		}
	};

	// 前端课程购买流程处理
	const handleCoursePurchaseFlow = async (userInput: string) => {
		console.log("(Course Search & Order Creation) for user:", userInput);
		
		// 第一步：立即显示搜索状态并同时开始后端调用
		const searchingMessage: Message = {
			text: `
<div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>🔍 Analyzing your request...</strong>
</div>`,
			sender: "ai",
			type: "html",
		};
		setMessages((prev) => [...prev, searchingMessage]);

		// 💡 关键优化：立即开始后端API调用（并行处理）
		const courseInfo = extractCourseInfo(userInput);
		const backendPromise = (async () => {
			try {
				console.log("⚡ 立即开始调用后端获取支付宝按钮...");
				const response = await fetch("/market-trade", {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
					},
					body: JSON.stringify({
						message: `Create a payment order for ${courseInfo.price_rmb.toFixed(2)} RMB to purchase ${courseInfo.name}, with order ID ${courseInfo.order_id}`
					}),
				});

				if (!response.ok) {
					throw new Error(`HTTP error! Status: ${response.status}`);
				}

				if (!response.body) {
					throw new Error("ReadableStream not supported");
				}

				// 获取response的ReadableStream
				const reader = response.body.getReader();
				const decoder = new TextDecoder();
				let streamText = "";

				// 读取流数据
				while (true) {
					const { done, value } = await reader.read();
					if (done) break;

					// 解码二进制数据为文本
					const chunk = decoder.decode(value, { stream: !done });
					streamText += chunk;
				}

				return streamText;

			} catch (error) {
				console.error("获取支付宝按钮失败:", error);
				throw error;
			}
		})();

		// 2秒后：显示搜索进度
		setTimeout(() => {
			const progressMessage: Message = {
				text: `
<div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>🔍 Searching for course and planning payment path...</strong>
</div>`,
				sender: "ai",
				type: "html",
			};
			setMessages((prev) => [...prev, progressMessage]);
		}, 2000);

		// 5秒后：显示课程详情
		setTimeout(() => {
			const courseDetailsMessage: Message = {
				text: `
<div class="payment-info-card" style="background-color: #2a2a2a; border: 1px solid #444; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
    <h3 style="color: #EAEAEA; border-bottom: 1px solid #444; padding-bottom: 10px;">📚 ${courseInfo.name}</h3>
    
    <div style="background: rgba(34, 197, 94, 0.1); border-left: 3px solid #22C55E; padding: 10px; margin: 15px 0; font-size: 0.9em; color: #94A3B8;">
        <strong>✅ Course found successfully!</strong><br>
        Platform: ${courseInfo.platform}<br>
        Duration: ${courseInfo.duration}<br>
        Level: ${courseInfo.level}<br>
        Instructor: ${courseInfo.instructor}
    </div>
    
    <!-- Course Preview Section -->
    <div style="background: rgba(0, 123, 255, 0.1); border: 1px solid rgba(0, 123, 255, 0.3); border-radius: 8px; padding: 15px; margin: 15px 0;">
        <h4 style="color: #4FC3F7; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-flex; align-items: center; font-size: 1.1em;">🔍</span>
            <span>Course Preview</span>
        </h4>
        <p style="color: #B0BEC5; font-size: 0.9em; margin-bottom: 12px;">
            Preview the course content and curriculum before purchase
        </p>
        <p style="margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-flex; align-items: center; font-size: 1.1em;">🌐</span>
            <a href="${courseInfo.preview_url}" 
               target="_blank" 
               rel="noopener noreferrer"
               style="color: #4FC3F7; text-decoration: none; font-weight: 600;">
                Visit edX Course Page ↗
            </a>
        </p>
        <div style="margin-top: 8px; font-size: 0.8em; color: #90A4AE; display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-flex; align-items: center; font-size: 1.1em;">📋</span>
            <span>Certificate: ${courseInfo.certificate}</span>
        </div>
    </div>
    
    <div class="course-description" style="margin: 15px 0; padding: 10px; background: rgba(0, 0, 0, 0.2); border-radius: 6px;">
        <h4 style="color: #EAEAEA; margin-bottom: 8px;">Course Description:</h4>
        <p style="color: #BDBDBD; line-height: 1.5;">${courseInfo.description}</p>
    </div>
    
    <div class="info-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px;">
        <div><strong style="color: #BDBDBD;">Course Price:</strong><br><span style="color: #FFFFFF;">$${courseInfo.price_usd.toFixed(2)} USD</span></div>
        <div><strong style="color: #BDBDBD;">Order ID:</strong><br><span style="color: #FFFFFF; font-family: 'Courier New', Courier, monospace;">${courseInfo.order_id}</span></div>
        <div><strong style="color: #BDBDBD;">Exchange Rate:</strong><br><span style="color: #FFFFFF;">1 USD ≈ 7.25 RMB</span></div>
        <div><strong style="color: #BDBDBD;">Total Amount:</strong><br><span style="color: #FFFFFF; font-weight: bold;">¥${courseInfo.price_rmb.toFixed(2)} RMB</span></div>
    </div>
    
    <div class="payment-path-container" style="margin: 24px 0; padding: 0; background: transparent; border-radius: 16px;">
        <h4 style="color: #EAEAEA; margin-bottom: 16px; font-size: 18px; font-weight: 600; display: flex; align-items: center; gap: 8px;">
            <span style="background: linear-gradient(135deg, #00FFD1, #6C40F7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">🔄 Payment Journey</span>
        </h4>
        
        <div class="payment-flow-steps" style="display: flex; align-items: stretch; justify-content: space-between; background: linear-gradient(135deg, rgba(31, 31, 42, 0.8), rgba(24, 24, 32, 0.9)); padding: 20px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); position: relative; overflow: hidden; min-height: 120px;">
            <!-- Background decoration -->
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #00FFD1 0%, #6C40F7 33%, #4A90E2 66%, #22C55E 100%);"></div>
            
            <!-- Step 1: Alipay -->
            <div class="payment-step" style="display: flex; flex-direction: column; align-items: center; justify-content: flex-start; flex: 1; position: relative; z-index: 2; padding-top: 10px;">
                <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #00FFD1, #00B8A3); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; box-shadow: 0 4px 16px rgba(0, 255, 209, 0.3); border: 2px solid rgba(255, 255, 255, 0.1); flex-shrink: 0;">
                    <span style="font-size: 20px; line-height: 1;">💰</span>
                </div>
                <div style="color: #00FFD1; font-weight: 600; font-size: 14px; text-align: center; margin-bottom: 4px; line-height: 1.2;">Alipay</div>
                <div style="color: #A0A0B4; font-size: 12px; text-align: center; line-height: 1.2;">RMB Payment</div>
            </div>
            
            <!-- Arrow 1 -->
            <div class="flow-arrow" style="flex: 0 0 auto; margin: 0 8px; color: #6C40F7; font-size: 18px; display: flex; align-items: center; justify-content: center; height: 100%; padding-top: 10px;">
                <svg width="24" height="16" viewBox="0 0 24 16" fill="none" style="filter: drop-shadow(0 2px 4px rgba(108, 64, 247, 0.3));">
                    <path d="M16 0L14.59 1.41L19.17 6H0V8H19.17L14.59 12.59L16 14L24 6L16 0Z" fill="currentColor"/>
                </svg>
            </div>
            
            <!-- Step 2: Stablecoin Transfer -->
            <div class="payment-step" style="display: flex; flex-direction: column; align-items: center; justify-content: flex-start; flex: 1; position: relative; z-index: 2; padding-top: 10px;">
                <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #6C40F7, #8B5CF6); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; box-shadow: 0 4px 16px rgba(108, 64, 247, 0.3); border: 2px solid rgba(255, 255, 255, 0.1); flex-shrink: 0;">
                    <span style="font-size: 20px; line-height: 1;">🔗</span>
                </div>
                <div style="color: #6C40F7; font-weight: 600; font-size: 14px; text-align: center; margin-bottom: 4px; line-height: 1.2;">Stablecoin Bridge</div>
                <div style="color: #A0A0B4; font-size: 12px; text-align: center; line-height: 1.2;">Cross-chain</div>
            </div>
            
            <!-- Arrow 2 -->
            <div class="flow-arrow" style="flex: 0 0 auto; margin: 0 8px; color: #4A90E2; font-size: 18px; display: flex; align-items: center; justify-content: center; height: 100%; padding-top: 10px;">
                <svg width="24" height="16" viewBox="0 0 24 16" fill="none" style="filter: drop-shadow(0 2px 4px rgba(74, 144, 226, 0.3));">
                    <path d="M16 0L14.59 1.41L19.17 6H0V8H19.17L14.59 12.59L16 14L24 6L16 0Z" fill="currentColor"/>
                </svg>
            </div>
            
            <!-- Step 3: PayPal -->
            <div class="payment-step" style="display: flex; flex-direction: column; align-items: center; justify-content: flex-start; flex: 1; position: relative; z-index: 2; padding-top: 10px;">
                <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #4A90E2, #2563EB); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; box-shadow: 0 4px 16px rgba(74, 144, 226, 0.3); border: 2px solid rgba(255, 255, 255, 0.1); flex-shrink: 0;">
                    <span style="font-size: 20px; line-height: 1;">💳</span>
                </div>
                <div style="color: #4A90E2; font-weight: 600; font-size: 14px; text-align: center; margin-bottom: 4px; line-height: 1.2;">PayPal</div>
                <div style="color: #A0A0B4; font-size: 12px; text-align: center; line-height: 1.2;">USD Settlement</div>
            </div>
            
            <!-- Arrow 3 -->
            <div class="flow-arrow" style="flex: 0 0 auto; margin: 0 8px; color: #22C55E; font-size: 18px; display: flex; align-items: center; justify-content: center; height: 100%; padding-top: 10px;">
                <svg width="24" height="16" viewBox="0 0 24 16" fill="none" style="filter: drop-shadow(0 2px 4px rgba(34, 197, 94, 0.3));">
                    <path d="M16 0L14.59 1.41L19.17 6H0V8H19.17L14.59 12.59L16 14L24 6L16 0Z" fill="currentColor"/>
                </svg>
            </div>
            
            <!-- Step 4: Course Access -->
            <div class="payment-step" style="display: flex; flex-direction: column; align-items: center; justify-content: flex-start; flex: 1; position: relative; z-index: 2; padding-top: 10px;">
                <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #22C55E, #16A34A); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 12px; box-shadow: 0 4px 16px rgba(34, 197, 94, 0.3); border: 2px solid rgba(255, 255, 255, 0.1); flex-shrink: 0;">
                    <span style="font-size: 20px; line-height: 1;">📚</span>
                </div>
                <div style="color: #22C55E; font-weight: 600; font-size: 14px; text-align: center; margin-bottom: 4px; line-height: 1.2;">Course Access</div>
                <div style="color: #A0A0B4; font-size: 12px; text-align: center; line-height: 1.2;">Instant Delivery</div>
            </div>
            
            <!-- Animated background particles -->
            <div style="position: absolute; top: 50%; left: 10%; width: 4px; height: 4px; background: #00FFD1; border-radius: 50%; opacity: 0.6;"></div>
            <div style="position: absolute; top: 30%; right: 20%; width: 3px; height: 3px; background: #6C40F7; border-radius: 50%; opacity: 0.4;"></div>
            <div style="position: absolute; bottom: 20%; left: 30%; width: 2px; height: 2px; background: #4A90E2; border-radius: 50%; opacity: 0.5;"></div>
        </div>
        
        <!-- Processing time indicator -->
        <div style="margin-top: 12px; text-align: center; color: #A0A0B4; font-size: 13px; font-weight: 500;">
            <span style="background: rgba(255, 255, 255, 0.05); padding: 4px 12px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1);">
                ⚡ Estimated completion: ~25 seconds
            </span>
        </div>
    </div>
</div>`,
				sender: "ai",
				type: "html",
			};
			setMessages((prev) => [...prev, courseDetailsMessage]);
		}, 5000);

		// 7秒后：显示正在创建支付宝订单
		setTimeout(() => {
			const orderCreationMessage: Message = {
				text: `
<div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 16px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8; position: relative; overflow: hidden;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div class="spinner" style="width: 20px; height: 20px; border: 2px solid rgba(139, 92, 246, 0.3); border-top: 2px solid #8B5CF6; border-radius: 50%; animation: spin 1s linear infinite;"></div>
        <div>
            <strong style="color: #A78BFA;">🔄 Creating your Alipay payment order...</strong><br>
            <span style="color: #94A3B8; font-size: 0.85em;">Backend processing almost complete...</span>
        </div>
    </div>
    
    <!-- 进度条动画 -->
    <div style="margin-top: 12px; background: rgba(139, 92, 246, 0.2); height: 4px; border-radius: 2px; overflow: hidden;">
        <div style="height: 100%; background: linear-gradient(90deg, #8B5CF6, #A78BFA); border-radius: 2px; animation: progress 2s ease-out forwards; width: 0%;"></div>
    </div>
    
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes progress {
            0% { width: 0%; }
            50% { width: 65%; }
            100% { width: 100%; }
        }
    </style>
</div>`,
				sender: "ai",
				type: "html",
			};
			setMessages((prev) => [...prev, orderCreationMessage]);
		}, 7000);

		// 优化：等待后端API完成（通常在7-9秒内完成）
		try {
			const streamText = await backendPromise;
			
			// 添加AI Agent的响应（支付宝按钮）
			const alipayButtonMessage: Message = {
				text: streamText.replace(/\n/g, "<br>").replace(/\r/g, ""),
				sender: "ai",
				type: "html",
			};
			setMessages((prev) => [...prev, alipayButtonMessage]);

		} catch (error) {
			console.error("获取支付宝按钮失败:", error);
			const errorMessage: Message = {
				text: `<div style="background: rgba(220, 38, 38, 0.1); border: 1px solid rgba(220, 38, 38, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; color: #F87171;">
					<strong>❌ Payment setup failed</strong><br>
					Please try again later.
				</div>`,
				sender: "ai",
				type: "html",
			};
			setMessages((prev) => [...prev, errorMessage]);
		} finally {
			setIsTyping(false);
		}
	};

	// 检测是否为课程购买请求
	const isCourseRequest = (message: string): boolean => {
		const keywords = ["purchase", "buy", "course", "want to buy", "希望购买", "课程", "learn", "training", "enroll"];
		return keywords.some(keyword => message.toLowerCase().includes(keyword));
	};

	// 响应消息
	const respondToMessage = async (message: string) => {
		setIsTyping(true);
		console.log("发送消息:", message);
		console.log("当前对话ID:", currentConversationId);
		console.log("选中的Agent:", selectedAgent);

		// 如果还没有对话，创建一个新对话
		if (!currentConversationId) {
			console.log("警告：没有当前对话ID，创建新对话");
			createNewConversation();
			// 等待状态更新
			await new Promise(resolve => setTimeout(resolve, 100));
		}

		// 特殊处理：检测课程购买请求且当前是trade agent
		if (selectedAgent === "trade" && isCourseRequest(message)) {
			console.log("检测到课程购买请求，启动前端流程");
			await handleCoursePurchaseFlow(message);
			return; // 直接返回，不调用后端API
		}

		// 创建新的AI消息但不填充内容
		const aiResponse: Message = {
			text: "",
			sender: "ai",
			type: "html",
		};
		console.log(messages, "messages---xxx");
		setMessages((prev) => [...prev, aiResponse]);

		try {
			// 根据选择的agent类型调用不同的API接口
			let apiEndpoint = "";
			if (selectedAgent === "shopping") {
				apiEndpoint = "/api/chat"; // Amazon购物助手 - 使用新的统一API
				console.log("使用Amazon Shopping Agent API");
			} else if (selectedAgent === "trade") {
				apiEndpoint = "/market-trade"; // 支付宝转代币助手
				console.log("使用Trade Agent API");
			} else {
				console.error("未知的Agent类型:", selectedAgent);
				throw new Error(`未知的Agent类型: ${selectedAgent}`);
			}

			console.log("API端点:", apiEndpoint);

			const response = await fetch(apiEndpoint, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					message: message
				}),
			});

			if (!response.ok) {
				throw new Error(`HTTP error! Status: ${response.status}`);
			}

			// 如果是购物助手，处理JSON响应
			if (selectedAgent === "shopping") {
				const data = await response.json();
				console.log("Amazon购物助手响应:", data);
				
				if (data.success && data.response) {
					// 直接使用response字段的内容，格式化换行符
					let formattedText = data.response
						.replace(/\n/g, "<br>") // 将\n替换为HTML的<br>标签
						.replace(/\r/g, ""); // 移除可能存在的\r字符

					console.log("格式化后的响应文本:", formattedText.substring(0, 200) + "...");

					// 更新UI上的消息
					setMessages((prev) => {
						const updatedMessages = [...prev];
						const lastMessage = updatedMessages[updatedMessages.length - 1];

						if (lastMessage && lastMessage.sender === "ai") {
							lastMessage.text = formattedText;
							console.log("✅ 成功更新AI消息内容");
						} else {
							console.error("❌ 没有找到要更新的AI消息");
						}

						return updatedMessages;
					});
				} else {
					console.error("❌ Amazon购物助手响应格式错误:", data);
					throw new Error(data.error || "Amazon购物助手响应失败");
				}
			} else {
				// 其他助手使用流式响应处理
				if (!response.body) {
					throw new Error("ReadableStream not supported");
				}

				// 获取response的ReadableStream
				const reader = response.body.getReader();
				const decoder = new TextDecoder();
				let streamText = "";

				// 读取流数据
				while (true) {
					const { done, value } = await reader.read();
					if (done) break;

					// 解码二进制数据为文本
					const chunk = decoder.decode(value, { stream: !done });
					streamText += chunk;

					// 更新UI上的消息
					setMessages((prev) => {
						const updatedMessages = [...prev];
						const lastMessage = updatedMessages[updatedMessages.length - 1];

						if (lastMessage && lastMessage.sender === "ai") {
							// 确保HTML内容中的换行符被正确处理
							let formattedText = streamText
								.replace(/\n/g, "<br>") // 将\n替换为HTML的<br>标签
								.replace(/\r/g, ""); // 移除可能存在的\r字符

							// 调试：输出接收到的HTML内容（仅在开发模式下）
							if (import.meta.env.DEV) {
								console.log("接收到的AI响应内容:", formattedText);
								
								// 检查是否包含按钮HTML
								if (formattedText.includes('confirm-btn-purple')) {
									console.log("检测到确认按钮HTML");
								}
							}

							lastMessage.text = formattedText;
						}

						return updatedMessages;
					});
				}
			}

			// 请求成功完成
			console.log("✅ API请求成功完成");
			setIsTyping(false);

		} catch (error) {
			console.error("❌ API请求错误:", error);
			setIsTyping(false);

			// 显示详细的错误信息
			let errorMessage = "Sorry, an error occurred. Please try again.";
			if (error instanceof Error) {
				console.error("错误详情:", error.message);
				// 在开发环境显示详细错误
				if (import.meta.env.DEV) {
					errorMessage = `开发模式错误: ${error.message}`;
				}
			}

			// 更新UI显示错误消息
			setMessages((prev) => {
				const updatedMessages = [...prev];
				const lastMessage = updatedMessages[updatedMessages.length - 1];

				if (lastMessage && lastMessage.sender === "ai") {
					lastMessage.text = `<p class='text-red-500 whitespace-pre-wrap'>${errorMessage}</p>`;
				}

				return updatedMessages;
			});
		}
	};



	// 添加按钮点击状态管理
	const [buttonClickedMap, setButtonClickedMap] = useState<Record<string, boolean>>({});

	// 前端自动化支付演示函数
	const startAutomatedPaymentDemo = () => {
		console.log("开始前端自动化支付演示");
		
		// 第一步：代币转账（立即开始）
		const stablecoinTransferMessage: Message = {
			text: `
<div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>⏳ Executing stablecoin transfer...</strong>
</div>`,
			sender: "ai",
			type: "html",
		};
		
		setMessages((prevMessages) => [...prevMessages, stablecoinTransferMessage]);
		
		// 8秒后：代币转账完成
		setTimeout(() => {
			const stablecoinSuccessMessage: Message = {
				text: `
<div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>✅ Stablecoin transfer completed!</strong><br>
    From: 0xE4949a0339320cE9ec93c9d0836c260F23DFE8Ca<br>
    To: 0xf874871Bc0f99a06b5327F34AceAa80Ae71905DE<br>
    Amount: 49.99 USDT<br>
    Tx Hash: 0x1a2b3c4d5e6f789012345678901234567890abcd<br>
    <em>Converting to merchant PayPal account...</em>
</div>`,
				sender: "ai",
				type: "html",
			};
			
			setMessages((prevMessages) => [...prevMessages, stablecoinSuccessMessage]);
			
			// 立即显示PayPal处理状态
			setTimeout(() => {
				const paypalProcessingMessage: Message = {
					text: `
<div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>⏳ Converting to merchant PayPal...</strong>
</div>`,
					sender: "ai",
					type: "html",
				};
				
				setMessages((prevMessages) => [...prevMessages, paypalProcessingMessage]);
			}, 100);
			
		}, 8000);

		// 13秒后：PayPal收款完成
		setTimeout(() => {
			const paypalSuccessMessage: Message = {
				text: `
<div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>✅ Merchant received payment!</strong><br>
    
    <div class="paypal-receipt" style="background: #f5f5f5; color: #333; padding: 15px; border-radius: 8px; margin: 10px 0; font-family: Arial, sans-serif;">
        <div style="text-align: center; margin-bottom: 15px;">
            <img src="https://www.paypalobjects.com/webstatic/icon/pp258.png" alt="PayPal" style="width: 80px;"/>
            <h3 style="margin: 10px 0; color: #0070ba;">Payment Receipt</h3>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 14px;">
            <div><strong>Transaction ID:</strong><br>7XB123456789</div>
            <div><strong>Amount:</strong><br>$49.99 USD</div>
            <div><strong>Status:</strong><br><span style="color: #00a020;">Completed</span></div>
            <div><strong>Date:</strong><br>${new Date().toLocaleDateString()}</div>
            <div><strong>From:</strong><br>payment-bridge@polyagent.ai</div>
            <div><strong>To:</strong><br>merchant@courseplatform.com</div>
        </div>
        
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
            <strong>Description:</strong> Primary Python Course<br>
            <strong>Merchant:</strong> edX Professional Education Services
        </div>
    </div>
    
    <em>Preparing your course access...</em>
</div>`,
				sender: "ai",
				type: "html",
			};
			
			setMessages((prevMessages) => [...prevMessages, paypalSuccessMessage]);
			
			// 立即显示课程交付准备状态
			setTimeout(() => {
				const deliveryProcessingMessage: Message = {
					text: `
<div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>⏳ Preparing course delivery...</strong>
</div>`,
					sender: "ai",
					type: "html",
				};
				
				setMessages((prevMessages) => [...prevMessages, deliveryProcessingMessage]);
			}, 100);
			
		}, 13000);

		// 18秒后：课程交付完成
		setTimeout(() => {
			const courseDeliveryMessage: Message = {
				text: `
<div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>🎉 Course access granted!</strong><br>
    
    <div class="course-delivery" style="background: #2a2a2a; border: 1px solid #444; border-radius: 8px; padding: 20px; margin: 15px 0;">
        <h3 style="color: #EAEAEA; margin-bottom: 15px;">📚 Your Course is Ready!</h3>
        
        <div style="background: rgba(0, 255, 209, 0.1); border-left: 3px solid #00FFD1; padding: 10px; margin: 15px 0;">
            <strong>Course:</strong> Primary Python Course<br>
            <strong>Platform:</strong> edX Professional Education<br>
            <strong>Access:</strong> Lifetime Access
        </div>
        
        <div style="background: rgba(74, 144, 226, 0.1); padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="color: #EAEAEA; margin-bottom: 8px; font-size: 16px;">
                <strong>📁 Your download link:</strong>
            </p>
            <p style="margin-bottom: 10px;">
                <a href="https://www.dropbox.com/scl/fo/qa0db0e4yfmaohrzox6ym/ADKAhnvn1GayIwqd_MPCsQE?rlkey=8rde0y77v3minbl9fbjsfsiqa&st=tohswbdl&dl=0" 
                   target="_blank" 
                   rel="noopener noreferrer"
                   style="color: #00FFD1; text-decoration: none; font-weight: 600; font-size: 14px; word-break: break-all;">
                    https://www.dropbox.com/scl/fo/qa0db0e4yfmaohrzox6ym/ADKAhnvn1GayIwqd_MPCsQE?rlkey=8rde0y77v3minbl9fbjsfsiqa&st=tohswbdl&dl=0
                </a>
            </p>
            
        </div>
        
        <div style="margin-top: 15px; font-size: 0.9em; color: #94A3B8;">
            <strong>📋 What's included:</strong><br>
            • Complete Primary Python video course (25+ hours)<br>
            • Python fundamentals and practice exercises<br>
            • Interactive Jupyter notebooks and code examples<br>
            • edX Verified Certificate of completion<br>
            • Python programming cheat sheets and resources<br>
            • Access to online Python community
        </div>
    </div>
</div>

<div style="background: rgba(74, 144, 226, 0.1); border: 1px solid rgba(74, 144, 226, 0.3); border-radius: 8px; padding: 16px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>✨ Cross-Border Payment Complete!</strong><br>
    Your payment journey: <strong>Alipay (CNY)</strong> → <strong>Stablecoin Bridge</strong> → <strong>PayPal (USD)</strong> → <strong>Course Access</strong><br>
    <span style="color: #00D084;">Total transaction time: ~18 seconds</span>
</div>`,
				sender: "ai",
				type: "html",
			};
			
			setMessages((prevMessages) => [...prevMessages, courseDeliveryMessage]);
			console.log("前端自动化支付演示流程完成！");
			
		}, 18000);

		// 确保每次添加消息后都滚动到底部
		const scrollToBottom = () => {
			setTimeout(() => {
				if (chatContainerRef.current) {
					chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
				}
			}, 100);
		};

		// 在每个消息添加后滚动
		setTimeout(scrollToBottom, 100);
		setTimeout(scrollToBottom, 8100);
		setTimeout(scrollToBottom, 13100);
		setTimeout(scrollToBottom, 18100);
	};

	// 全局函数，供HTML按钮调用
	useEffect(() => {
		// 支付宝支付处理函数
		(window as any).handleAlipayPayment = (linkElement: HTMLAnchorElement) => {
			console.log("支付宝支付按钮被点击，将在10秒后自动开始前端动画演示。");
			
			// 1. 打开支付链接
			if (linkElement.href && linkElement.href !== "[支付链接]") {
				window.open(linkElement.href, '_blank');
			}
			
			// 2. 禁用按钮，防止重复点击
			linkElement.style.pointerEvents = 'none';
			linkElement.style.opacity = '0.5';
			linkElement.textContent = 'Processing...';

			// 3. 10秒后显示支付宝成功消息并开始前端自动化流程
			setTimeout(() => {
				const alipaySuccessMessage: Message = {
					text: `
<div style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 6px; padding: 12px; margin: 1rem 0; font-size: 0.9em; color: #94A3B8;">
    <strong>✅ Alipay payment successful!</strong><br>
    Amount: ¥362.43 RMB<br>
    Transaction ID: 2025010712345678<br>
    <em>Now initiating stablecoin transfer...</em>
</div>`,
					sender: "ai",
					type: "html",
				};
				
				setMessages((prevMessages) => [...prevMessages, alipaySuccessMessage]);

				// 滚动到聊天底部
				setTimeout(() => {
					if (chatContainerRef.current) {
						chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
					}
				}, 100);

				// 1秒后开始前端自动化演示流程
				setTimeout(() => {
					startAutomatedPaymentDemo();
				}, 1000);

			}, 10000); // 10秒延迟
		};

		// 新的自动化支付确认处理函数
		(window as any).handlePaymentConfirmation = () => {
			console.log("自动化支付确认按钮被点击");
			
			// 立即发送confirm_payment消息到后端触发自动化流程
			respondToMessage("confirm_payment");
		};

		(window as any).showTransferForm = (buttonId?: string) => {
			console.log("确认按钮被点击, buttonId:", buttonId);
			console.log("当前对话ID:", currentConversationId);
			console.log("选中的Agent:", selectedAgent);

			// 生成唯一的按钮ID（如果没有提供）
			const uniqueButtonId = buttonId || `btn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

			// 检查按钮是否已经被点击过
			if (buttonClickedMap[uniqueButtonId]) {
				console.log("按钮已被点击过，忽略重复点击");
				return;
			}

			// 标记按钮为已点击
			setButtonClickedMap(prev => ({
				...prev,
				[uniqueButtonId]: true
			}));

			// 提示用户需要手动输入确认信息，而不是自动执行
			console.log("按钮已点击，请在聊天框中输入确认信息以继续下一步");
		};

		return () => {
			delete (window as any).handleAlipayPayment;
			delete (window as any).handlePaymentConfirmation;
			delete (window as any).showTransferForm;
		};
	}, [currentConversationId, selectedAgent, setMessages, respondToMessage, buttonClickedMap]);

	// 发送消息
	const handleSendMessage = () => {
		if (inputMessage.trim()) {
			const newMessage = { text: inputMessage, sender: "user" as const };
			setMessages((prev) => [...prev, newMessage]);

			// 保存当前输入的消息内容
			const currentMessage = inputMessage;

			// 清空输入框
			setInputMessage("");

			// 滚动到底部
			setTimeout(() => {
				if (chatContainerRef.current) {
					chatContainerRef.current.scrollTop =
						chatContainerRef.current.scrollHeight;
				}
			}, 100);

			// 发送消息到服务端并处理响应
			respondToMessage(currentMessage);

			// 自动调整输入框高度
			if (textareaRef.current) {
				textareaRef.current.style.height = "auto";
			}
		}
	};

	// 自动调整文本区域高度
	const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
		setInputMessage(e.target.value);
		e.target.style.height = "auto";
		e.target.style.height = `${e.target.scrollHeight}px`;
	};

	// 处理键盘事件
	const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			handleSendMessage();
		}
	};

	// 滚动到底部
	useEffect(() => {
		if (chatContainerRef.current) {
			chatContainerRef.current.scrollTop =
				chatContainerRef.current.scrollHeight;
		}
	}, [messages, isTyping]);

	return (
		<WagmiProvider config={config}>
			<QueryClientProvider client={queryClient}>
				<RainbowKitProvider>
					<div className="app-container min-h-screen text-text-primary relative noise-bg">
						{/* Stagewise Toolbar - Development Only */}
						{StagewiseToolbar && ReactPlugin && (
							<StagewiseToolbar 
								config={{
									plugins: [ReactPlugin]
								}}
							/>
						)}
						{/* 粒子背景 */}
						<div className="particles" id="particles"></div>

						{/* 头部 */}
						<header className="sticky top-0 z-50 backdrop-blur-xl bg-bg-dark/80 border-b border-night-purple/20">
							<div className="container mx-auto px-4 py-3 flex justify-between items-center">
								<div className="flex items-center space-x-2">
									<div
										className="w-8 h-8 relative cursor-pointer hover:scale-110 transition-transform duration-300"
										onClick={() => setShowLogoOverlay(true)}
									>
										<div className="absolute inset-0 bg-gradient-to-br from-neon-cyan to-night-purple rounded-lg opacity-70 animate-pulse-slow"></div>
										<div className="absolute inset-0.5 bg-deep-black rounded-lg flex items-center justify-center">
											<span className="text-neon-cyan font-bold text-xl glow-text">
												P
											</span>
										</div>
									</div>
									<h1 className="text-xl font-bold tracking-tight">
										InterAgent
										{/* <span className="text-neon-cyan">.AI</span> */}
									</h1>
								</div>

								{/* AI助手切换按钮组 */}
								<div className="flex items-center space-x-1 bg-deep-black/50 backdrop-blur-md border border-night-purple/20 rounded-lg p-1 agent-switch-container">
														<button
						onClick={() => handleAgentSwitch("shopping")}
						onMouseEnter={(e) => handleMouseEnter("shopping", e)}
						onMouseLeave={handleMouseLeave}
						disabled={isAgentSwitching}
						className={`agent-switch-button relative px-4 py-2 rounded-md font-medium text-sm transition-all duration-300 ${selectedAgent === "shopping"
							? "bg-gradient-to-r from-neon-cyan/20 to-night-purple/20 text-neon-cyan border border-neon-cyan/30 shadow-lg agent-switch-active"
							: "text-text-secondary hover:text-text-primary hover:bg-white/5"
							} ${isAgentSwitching ? "opacity-50 cursor-not-allowed agent-switching" : ""}`}
					>
						{isAgentSwitching && selectedAgent === "shopping" && (
							<div className="absolute inset-0 rounded-md bg-gradient-to-r from-neon-cyan/10 to-night-purple/10 animate-pulse"></div>
						)}
						<span className="relative flex items-center space-x-2">
							<span className="agent-switch-icon">🛍️</span>
							<span className="hidden sm:inline">Shopping</span>
							<span className="sm:hidden">Shop</span>
						</span>
					</button>

														<button
						onClick={() => handleAgentSwitch("trade")}
						onMouseEnter={(e) => handleMouseEnter("trade", e)}
						onMouseLeave={handleMouseLeave}
						disabled={isAgentSwitching}
						className={`agent-switch-button relative px-4 py-2 rounded-md font-medium text-sm transition-all duration-300 ${selectedAgent === "trade"
							? "bg-gradient-to-r from-neon-cyan/20 to-night-purple/20 text-neon-cyan border border-neon-cyan/30 shadow-lg agent-switch-active"
							: "text-text-secondary hover:text-text-primary hover:bg-white/5"
							} ${isAgentSwitching ? "opacity-50 cursor-not-allowed agent-switching" : ""}`}
					>
						{isAgentSwitching && selectedAgent === "trade" && (
							<div className="absolute inset-0 rounded-md bg-gradient-to-r from-neon-cyan/10 to-night-purple/10 animate-pulse"></div>
						)}
						<span className="relative flex items-center space-x-2">
							<span className="agent-switch-icon">💰</span>
							<span className="hidden sm:inline">Payment Bridge</span>
							<span className="sm:hidden">Payment</span>
						</span>
					</button>
								</div>

								<div className="flex items-center space-x-4">
									{/* RainbowKit 钱包连接按钮 */}
									<div className="wallet-connect-btn">
										<ConnectButton label="Connect  Wallet" />
									</div>
								</div>
							</div>
						</header>

						<div className="container mx-auto flex flex-col md:flex-row min-h-[calc(100vh-57px)]">
							{/* 侧边栏 */}
							<aside className="md:w-64 bg-deep-black/50 backdrop-blur-md border-r border-night-purple/20 p-4 hidden md:block">
								<button
									onClick={createNewConversation}
									className="w-full px-4 py-2 mb-6 rounded-md bg-gradient-to-r from-neon-cyan/20 to-night-purple/20 hover:from-neon-cyan/30 hover:to-night-purple/30 border border-neon-cyan/30 text-neon-cyan flex items-center justify-center space-x-2 transition-all shine-effect"
								>
									<FontAwesomeIcon icon={faPlus} className="text-xs" />
									<span>New Chat</span>
								</button>
								<div className="space-y-1 mb-6">
									<h3 className="text-text-secondary text-xs uppercase tracking-wider mb-2 px-2">
										Recent Conversations
									</h3>

									{conversations.length > 0 ? (
										conversations.map((conv) => (
											<div
												key={conv.id}
												className={`conversation-item group relative w-full text-left px-3 py-2 rounded-md transition-all flex items-center justify-between ${currentConversationId === conv.id ? "bg-white/5" : ""
													}`}
											>
												{/* 对话内容区域 */}
												<button
													className="flex items-center space-x-3 flex-1 min-w-0"
													onClick={() => {
														selectConversation(conv.id);
													}}
												>
													<FontAwesomeIcon
														icon={faCommentAlt}
														className={`text-xs flex-shrink-0 ${currentConversationId === conv.id
															? "text-neon-cyan"
															: "text-text-secondary"
															}`}
													/>
													<span className="text-sm truncate">{conv.title}</span>
												</button>

												{/* 删除按钮 - 悬浮时显示 */}
												<button
													onClick={(e) => deleteConversation(conv.id, e)}
													className="delete-conversation-btn opacity-0 group-hover:opacity-100 transition-all duration-200 w-6 h-6 rounded-md bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 hover:border-red-500/40 flex items-center justify-center ml-2 flex-shrink-0"
													title="删除对话"
												>
													<FontAwesomeIcon
														icon={faTimes}
														className="delete-conversation-icon text-xs text-red-400 hover:text-red-300"
													/>
												</button>
											</div>
										))
									) : (
																			<div className="text-text-secondary text-sm px-3 py-2">
										No conversations yet
									</div>
									)}
								</div>

								<div className="space-y-1">
									<h3 className="text-text-secondary text-xs uppercase tracking-wider mb-2 px-2">
										Workspace
									</h3>

									{/* <button className="w-full text-left px-3 py-2 rounded-md hover:bg-white/5 transition-all flex items-center space-x-3">
										<FontAwesomeIcon
											icon={faBolt}
											className="text-text-secondary text-xs"
										/>
										<span className="text-sm truncate">My Collection</span>
                  </button> */}

                  <button
                    onClick={() => setShowSignaturePanel(!showSignaturePanel)}
                    className="w-full text-left px-3 py-2 rounded-md hover:bg-white/5 transition-all flex items-center space-x-3"
                  >
                    <FontAwesomeIcon
                      icon={faSignature}
                      className="text-text-secondary text-xs"
                    />
                    <span className="text-sm truncate">Wallet Signature</span>
									</button>
                  {/* 
									<button className="w-full text-left px-3 py-2 rounded-md hover:bg-white/5 transition-all flex items-center space-x-3">
										<FontAwesomeIcon
											icon={faHistory}
											className="text-text-secondary text-xs"
										/>
										<span className="text-sm truncate">historical records</span>
									</button>

									<button className="w-full text-left px-3 py-2 rounded-md hover:bg-white/5 transition-all flex items-center space-x-3">
										<FontAwesomeIcon
											icon={faCog}
											className="text-text-secondary text-xs"
										/>
										<span className="text-sm truncate">set up</span>
									</button> */}


								</div>

                {/* 签名工具面板 */}
                {showSignaturePanel && (
                  <div className="mt-4">
                    <WalletSignature />
                  </div>
                )}
							</aside>

							{/* 主要内容 */}
							<main className="flex-1 flex flex-col relative">
								{/* 聊天容器 */}
								<div
									className="agent-container flex-1 overflow-y-auto px-4 py-6 space-y-6 pb-0"
									ref={chatContainerRef}
								>
									{/* 历史消息 */}
									{messages.map((msg, index) => (
										<div key={index} className="max-w-3xl mx-auto">
											{msg.sender === "user" ? (
												<div className="user-message mb-6 rounded-tr-lg rounded-b-lg bg-deep-black/50 backdrop-blur-sm p-4 ml-8">
													<div className="flex items-center mb-2">
														<p className="text-sm text-text-secondary">user</p>
													</div>
													<p>{msg.text}</p>
												</div>
											) : (
												<div className="ai-message mb-6 rounded-tl-lg rounded-b-lg bg-gradient-to-br from-deep-black/90 to-bg-dark/90 backdrop-blur-sm p-4 mr-8">
													<div className="flex items-center mb-2">
														<div className="w-8 h-8 relative mr-4">
															<div className="absolute inset-0 bg-gradient-to-br from-neon-cyan/40 to-night-purple/40 rounded-full opacity-70"></div>
															<div className="absolute inset-0.5 bg-deep-black rounded-full flex items-center justify-center">
																<span className="text-neon-cyan text-xs font-bold">
																	P
																</span>
															</div>
														</div>
														<p className="text-sm text-text-secondary">
															InterAgent
														</p>
													</div>
													{msg.type === "html" ? (
														<div
															className="ai-response-content whitespace-pre-wrap"
															dangerouslySetInnerHTML={{ __html: msg.text }}
														></div>
													) : (
														<p>{msg.text}</p>
													)}
												</div>
											)}
										</div>
									))}

									{/* 打字指示器 */}
									{isTyping && (
										<div className="max-w-3xl mx-auto">
											<div className="ai-message mb-6 rounded-tl-lg rounded-b-lg bg-gradient-to-br from-deep-black/90 to-bg-dark/90 backdrop-blur-sm p-4 mr-8">
												<div className="flex space-x-2">
													<span
														className="w-2 h-2 bg-neon-cyan/50 rounded-full animate-bounce"
														style={{ animationDelay: "0ms" }}
													></span>
													<span
														className="w-2 h-2 bg-neon-cyan/50 rounded-full animate-bounce"
														style={{ animationDelay: "300ms" }}
													></span>
													<span
														className="w-2 h-2 bg-neon-cyan/50 rounded-full animate-bounce"
														style={{ animationDelay: "600ms" }}
													></span>
												</div>
											</div>
										</div>
									)}
								</div>


								{/* 输入区域 */}
								<div className="user-input-container border-t border-night-purple/20 bg-deep-black/50 backdrop-blur-md p-4">
									<div className="mx-auto relative">
										<div className="relative gradient-border">
											<div className="flex items-center bg-deep-black rounded-md overflow-hidden input-active">
																				<textarea
									ref={textareaRef}
									rows={1}
									placeholder="Ask me anything about crypto or payments..."
									className="flex-1 resize-none bg-transparent border-none outline-none p-3 pr-12 text-text-primary placeholder-text-secondary/50"
									style={{ height: "48px", maxHeight: "200px" }}
									value={inputMessage}
									onChange={handleTextareaChange}
									onKeyDown={handleKeyDown}
								></textarea>

												<div className="absolute right-2 bottom-2 flex items-center">
													<button className="w-8 h-8 rounded-md text-text-secondary hover:text-neon-cyan flex items-center justify-center transition-colors">
														<FontAwesomeIcon icon={faMicrophone} />
													</button>
													<button
														onClick={handleSendMessage}
														className="w-8 h-8 rounded-md bg-gradient-to-r from-neon-cyan to-night-purple text-deep-black flex items-center justify-center ml-1"
													>
														<FontAwesomeIcon icon={faPaperPlane} />
													</button>
												</div>
											</div>
										</div>
									</div>
								</div>
							</main>
						</div>



						{/* Logo 放大覆盖层 */}
						{showLogoOverlay && (
							<div
								className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md"
								onClick={() => setShowLogoOverlay(false)}
							>
								<div
									className="relative animate-fade-in"
									onClick={(e) => e.stopPropagation()}
								>
									{/* 关闭按钮 */}
									<button
										className="absolute -top-10 -right-10 w-8 h-8 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center text-white/70 hover:text-white transition-all"
										onClick={() => setShowLogoOverlay(false)}
									>
										<span className="text-xl">×</span>
									</button>

									{/* 放大的 Logo */}
									<div className="w-80 h-80 relative logo-enlarged">
										<div className="absolute inset-0 bg-gradient-to-br from-neon-cyan to-night-purple rounded-3xl opacity-70 animate-pulse-slow shadow-2xl shadow-neon-cyan/30"></div>
										<div className="absolute inset-2 bg-deep-black rounded-3xl flex items-center justify-center border border-white/10">
											<span className="text-neon-cyan font-bold text-9xl glow-text drop-shadow-2xl">
												P
											</span>
										</div>
									</div>

									{/* Logo 信息 */}
									<div className="mt-6 text-center text-white/90">
										<h2 className="text-2xl font-bold mb-2">InterAgent</h2>
										<p className="text-sm text-white/70">Web3 AI Agent Interoperability Protocol</p>
										<p className="text-xs text-white/50 mt-2">320x320 pixels - Ready for icon processing</p>
									</div>
								</div>
							</div>
						)}

						{/* Agent Tooltip */}
						{showTooltip.show && showTooltip.agent && (
							<div
								className="fixed z-[60] pointer-events-none transform -translate-x-1/2"
								style={{
									left: `${showTooltip.position.x}px`,
									top: `${showTooltip.position.y}px`,
								}}
							>
								<div className="agent-tooltip animate-fade-in">
									{/* Tooltip 箭头 */}
									<div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
										<div className="w-0 h-0 border-l-[8px] border-l-transparent border-r-[8px] border-r-transparent border-b-[8px] border-b-gray-800"></div>
										<div className="absolute top-1 left-1/2 transform -translate-x-1/2">
											<div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[6px] border-b-deep-black"></div>
										</div>
									</div>

									{/* Tooltip 内容 */}
									<div className="bg-gradient-to-br from-deep-black/95 to-bg-dark/95 backdrop-blur-xl border border-night-purple/30 rounded-xl p-4 min-w-[280px] max-w-[320px] shadow-2xl shadow-night-purple/20">
										<div className="space-y-3">
											{/* 标题 */}
											<div className="flex items-center space-x-2">
												<h3 className="text-lg font-bold text-text-primary">
													{getAgentDescription(showTooltip.agent).title}
												</h3>
											</div>

											{/* 描述 */}
											<p className="text-sm text-text-secondary leading-relaxed">
												{getAgentDescription(showTooltip.agent).description}
											</p>

											{/* 功能特性 */}
											<div className="space-y-2">
												{getAgentDescription(showTooltip.agent).features.map((feature, index) => (
													<div key={index} className="flex items-start space-x-2 text-sm">
														<div className="w-1.5 h-1.5 rounded-full bg-neon-cyan mt-2 flex-shrink-0"></div>
														<span className="text-text-secondary leading-relaxed">{feature}</span>
													</div>
												))}
											</div>

											{/* 提示 */}
											<div className="mt-3 pt-3 border-t border-night-purple/20">
												<p className="text-xs text-text-secondary/80 italic">
													Click to switch to this assistant
												</p>
											</div>
										</div>
									</div>
								</div>
							</div>
						)}
					</div>
				</RainbowKitProvider>
			</QueryClientProvider>
		</WagmiProvider>
	);
}

export default App;