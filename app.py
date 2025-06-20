from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sys
import os
import traceback
from datetime import datetime
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# 修改为导入原始Amazon Agent（现在已经是同步实现）
from AgentCore.Society.amazon_shopping_agent_qwen3 import AmazonShoppingAgentQwen3, ThinkingMode

app = Flask(__name__)
CORS(app)

# 配置JSON以正确显示中文，避免Unicode转义
app.config['JSON_AS_ASCII'] = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局agent实例字典，支持多用户多会话
shopping_agents = {}

def get_shopping_agent(user_id: str = "default_user", session_id: str = None):
    """获取或创建Amazon购物助手实例"""
    global shopping_agents
    
    # 生成agent key
    agent_key = f"{user_id}:{session_id}" if session_id else f"{user_id}:default"
    
    if agent_key not in shopping_agents:
        try:
            # 创建新的Amazon Agent实例（原生Qwen3版本，同步实现）
            shopping_agents[agent_key] = AmazonShoppingAgentQwen3(
                thinking_mode=ThinkingMode.AUTO,
                user_id=user_id,
                session_id=session_id
            )
            
            logger.info(f"🤖 创建新的Amazon购物助手实例: {agent_key}")
            print(f"🤖 创建新的Amazon购物助手实例: {agent_key}")
        except Exception as e:
            logger.error(f"❌ 创建Amazon购物助手失败: {e}")
            print(f"❌ 创建Amazon购物助手失败: {e}")
            return None
    
    return shopping_agents[agent_key]

@app.route('/')
def index():
    """主页"""
    return jsonify({
        'status': 'ok',
        'message': 'InterAgent Amazon购物助手 - Qwen3原生版本 (同步实现)',
        'version': '3.0-native',
        'agent_type': 'Amazon Shopping Agent with Qwen3 Native (Sync)',
        'features': [
            'Amazon商品搜索与购买（原生Qwen3实现）',
            '支持qwen-agent MCP工具调用',
            'Qwen3-32B智能推理和思考模式',
            '多思考模式支持（启用/禁用/自动）',
            '完整的多轮对话历史管理',
            '购物状态追踪和管理',
            '多用户多会话支持',
            '同步实现，完全兼容Flask',
            '模拟MCP工具响应（降级处理）'
        ],
        'endpoints': {
            'chat': '/api/chat',
            'history': '/api/conversation/history',
            'clear': '/api/conversation/clear',
            'health': '/api/health',
            'status': '/api/status',
            'sessions': {
                'new': '/api/sessions/new',
                'list': '/api/sessions/list',
                'delete': '/api/sessions/{session_id}',
                'history': '/api/sessions/{session_id}/history',
                'clear': '/api/sessions/{session_id}/clear'
            }
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求，支持多轮对话和Amazon购物功能（同步实现）"""
    try:
        # 验证请求格式
        data = request.get_json()
        if not data or 'message' not in data:
            logger.warning("❌ 请求格式错误，缺少message字段")
            return jsonify({
                'success': False,
                'error': '请求格式错误，缺少message字段',
                'error_type': 'invalid_request'
            }), 400

        user_message = data['message'].strip()
        if not user_message:
            logger.warning("❌ 消息内容为空")
            return jsonify({
                'success': False,
                'error': '消息内容不能为空',
                'error_type': 'empty_message'
            }), 400

        # 获取用户ID和会话ID（可选参数）
        user_id = data.get('user_id', 'default_user')
        session_id = data.get('session_id', None)

        logger.info(f"🔍 [{datetime.now().strftime('%H:%M:%S')}] 用户 {user_id} 会话 {session_id} 发送消息: {user_message}")
        print(f"🔍 [{datetime.now().strftime('%H:%M:%S')}] 用户 {user_id} 会话 {session_id} 发送消息: {user_message}")

        # 获取Amazon购物助手实例
        agent = get_shopping_agent(user_id, session_id)
        
        if agent is None:
            logger.error("❌ Amazon购物助手初始化失败")
            return jsonify({
                'success': False,
                'error': 'Amazon购物助手服务暂时不可用，请稍后重试',
                'error_type': 'agent_unavailable'
            }), 503
        
        # 处理用户请求（同步调用，已修复异步问题）
        try:
            # 直接调用同步方法，不再使用asyncio.run
            result = agent.process_request(user_message)
            
            logger.info(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Amazon Agent响应生成完成")
            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Amazon Agent响应生成完成")
            
            # 获取对话历史统计和购物状态
            history = agent.get_conversation_history()
            shopping_state = agent.get_shopping_state()
            
            conversation_stats = {
                'total_turns': len(history),
                'mcp_available': shopping_state.get('mcp_available', False),
                'thinking_mode': shopping_state.get('thinking_mode', 'auto'),
                'current_state': shopping_state.get('current_state', 'browsing')
            }
            
            return jsonify({
                'success': True,
                'response': result,
                'conversation_stats': conversation_stats,
                'shopping_state': shopping_state,
                'session_id': agent.session_id,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Amazon Agent处理请求时出错: {e}")
            print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Amazon Agent处理请求时出错: {e}")
            print(f"🔍 详细错误信息: {traceback.format_exc()}")
            
            # 生成简单的错误响应
            fallback_response = f"""抱歉，处理您的请求"{user_message}"时遇到技术问题。请稍后重试或重新描述您的需求。
            
🔧 您可以尝试：
- 重新描述您的需求
- 使用更简单的表达方式
- 稍后重试

我仍然可以为您提供Amazon购物建议和模拟搜索服务。"""

            # 尝试记录对话历史
            try:
                agent.conversation_manager.add_turn(user_message, fallback_response)
            except:
                pass
            
            # 根据错误类型提供不同的错误信息
            error_msg = str(e).lower()
            if "openai" in error_msg or "api" in error_msg:
                error_type = "api_error"
            elif "model" in error_msg or "qwen" in error_msg:
                error_type = "model_error"
            elif "connection" in error_msg or "network" in error_msg:
                error_type = "connection_error"
            elif "timeout" in error_msg:
                error_type = "timeout"
            else:
                error_type = "processing_error"
            
            return jsonify({
                'success': True,  # 仍然返回success=True因为我们提供了有用的响应
                'response': fallback_response,
                'conversation_stats': {'total_turns': len(agent.get_conversation_history())},
                'shopping_state': {'error': True, 'error_type': error_type},
                'timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        logger.error(f"❌ [{datetime.now().strftime('%H:%M:%S')}] API错误: {e}")
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] API错误: {e}")
        print(f"🔍 详细错误信息: {traceback.format_exc()}")
        
        # 最后的兜底响应
        return jsonify({
            'success': False,
            'error': 'Amazon购物助手服务暂时不可用，请稍后重试',
            'error_type': 'server_error',
            'fallback_response': '您好！Amazon购物助手当前遇到技术问题，请稍后重试。',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/conversation/history', methods=['GET'])
def get_conversation_history():
    """获取对话历史"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        session_id = request.args.get('session_id', None)
        
        agent = get_shopping_agent(user_id, session_id)
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Amazon购物助手服务不可用'
            }), 503
            
        history = agent.get_conversation_history()
        
        # 转换为可序列化的格式
        history_data = []
        for turn in history:
            history_data.append({
                'user_input': turn.user_input,
                'ai_response': turn.ai_response,
                'timestamp': turn.timestamp.isoformat(),
                'shopping_state': turn.shopping_state.value,
                'tools_used': turn.tools_used,
                'thinking_content': turn.thinking_content[:200] + "..." if len(turn.thinking_content) > 200 else turn.thinking_content
            })
        
        return jsonify({
            'success': True,
            'history': history_data,
            'total_turns': len(history_data),
            'shopping_state': agent.get_shopping_state(),
            'session_id': agent.session_id,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"❌ 获取对话历史失败: {e}")
        print(f"❌ 获取对话历史失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取对话历史失败: {str(e)}'
        }), 500

@app.route('/api/conversation/clear', methods=['POST'])
def clear_conversation():
    """清除对话历史"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'default_user')
        session_id = data.get('session_id', None)
        
        agent = get_shopping_agent(user_id, session_id)
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Amazon购物助手服务不可用'
            }), 503
            
        agent.clear_conversation_history()
        
        logger.info(f"🧹 Amazon购物助手对话历史已清除: {user_id}:{session_id}")
        print(f"🧹 Amazon购物助手对话历史已清除: {user_id}:{session_id}")
        return jsonify({
            'success': True,
            'message': 'Amazon购物助手对话历史已清除，开始新的购物之旅吧！',
            'session_id': agent.session_id,
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"❌ 清除对话历史失败: {e}")
        print(f"❌ 清除对话历史失败: {e}")
        return jsonify({
            'success': False,
            'error': f'清除对话历史失败: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        agent = get_shopping_agent(user_id)
        
        if agent is None:
            return jsonify({
                'success': False,
                'status': 'unhealthy',
                'error': 'Amazon购物助手初始化失败',
                'timestamp': datetime.now().isoformat()
            }), 503
            
        history_count = len(agent.get_conversation_history())
        shopping_state = agent.get_shopping_state()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'agent_type': 'Amazon Shopping Agent Qwen3 Native (Sync)',
            'conversation_turns': history_count,
            'shopping_state': shopping_state,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取详细的服务状态"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        agent = get_shopping_agent(user_id)
        
        basic_status = {
            'timestamp': datetime.now().isoformat(),
            'agent_initialized': agent is not None,
            'agent_type': 'Amazon Shopping Agent Qwen3 Native (Sync)',
            'uptime': 'running',
            'active_agents': len(shopping_agents),
            'implementation': 'synchronous',
            'framework': 'qwen3_native',
            'mcp_support': 'qwen_agent'
        }
        
        if agent is not None:
            shopping_state = agent.get_shopping_state()
            basic_status.update(shopping_state)
            basic_status['conversation_turns'] = len(agent.get_conversation_history())
        
        return jsonify({
            'success': True,
            'status': basic_status
        })
        
    except Exception as e:
        logger.error(f"❌ 获取状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# 会话管理API端点
@app.route('/api/sessions/new', methods=['POST'])
def create_new_session():
    """创建新会话"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'default_user')
        title = data.get('title', None)
        
        # 获取或创建agent实例
        agent = get_shopping_agent(user_id)
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Amazon购物助手服务不可用'
            }), 503
        
        # 创建新会话
        session_id = agent.create_new_session(title)
        if session_id:
            logger.info(f"🆕 创建新会话: {user_id}:{session_id}")
            return jsonify({
                'success': True,
                'session_id': session_id,
                'user_id': user_id,
                'title': title or f"对话 {datetime.now().strftime('%m-%d %H:%M')}",
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': '创建新会话失败'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ 创建新会话失败: {e}")
        return jsonify({
            'success': False,
            'error': f'创建新会话失败: {str(e)}'
        }), 500

@app.route('/api/sessions/list', methods=['GET'])
def get_sessions_list():
    """获取用户的会话列表"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        # 获取agent实例
        agent = get_shopping_agent(user_id)
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Amazon购物助手服务不可用'
            }), 503
        
        # 获取会话列表
        sessions = agent.get_sessions_list()
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'user_id': user_id,
            'total_sessions': len(sessions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ 获取会话列表失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取会话列表失败: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除指定会话"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'default_user')
        
        # 获取agent实例
        agent = get_shopping_agent(user_id)
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Amazon购物助手服务不可用'
            }), 503
        
        # 删除会话
        success = agent.delete_session(session_id)
        
        if success:
            # 同时从内存中移除agent实例
            agent_key = f"{user_id}:{session_id}"
            if agent_key in shopping_agents:
                del shopping_agents[agent_key]
            
            logger.info(f"🗑️ 删除会话: {user_id}:{session_id}")
            return jsonify({
                'success': True,
                'message': f'会话 {session_id} 已删除',
                'session_id': session_id,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': '删除会话失败'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ 删除会话失败: {e}")
        return jsonify({
            'success': False,
            'error': f'删除会话失败: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """获取指定会话的对话历史"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        # 获取agent实例
        agent = get_shopping_agent(user_id, session_id)
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Amazon购物助手服务不可用'
            }), 503
        
        # 获取会话历史
        history = agent.get_session_conversation_history()
        
        return jsonify({
            'success': True,
            'history': history,
            'session_id': session_id,
            'user_id': user_id,
            'message_count': len(history),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ 获取会话历史失败: {e}")
        return jsonify({
            'success': False,
            'error': f'获取会话历史失败: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>/clear', methods=['POST'])
def clear_session_history(session_id):
    """清除指定会话的对话历史"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', 'default_user')
        
        # 获取agent实例
        agent = get_shopping_agent(user_id, session_id)
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Amazon购物助手服务不可用'
            }), 503
        
        # 清除会话历史
        agent.clear_conversation_history()
        
        logger.info(f"🧹 清除会话历史: {user_id}:{session_id}")
        return jsonify({
            'success': True,
            'message': f'会话 {session_id} 的历史记录已清除',
            'session_id': session_id,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ 清除会话历史失败: {e}")
        return jsonify({
            'success': False,
            'error': f'清除会话历史失败: {str(e)}'
        }), 500

# 兼容旧的API端点
@app.route("/youxuan-shopping", methods=["POST"])
def handle_youxuan_shopping():
    """兼容旧的购物请求端点，现在使用Amazon Agent Native"""
    try:
        data = request.json
        if not data or "message" not in data:
            return jsonify({"error": "请求体中缺少'message'字段"}), 400
        
        # 重定向到新的chat API（现在使用Amazon Agent Native）
        return chat()
        
    except Exception as e:
        logger.error(f"❌ 处理旧接口请求失败: {e}")
        return jsonify({"error": f"处理请求失败: {str(e)}"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '请求的资源不存在',
        'available_endpoints': [
            '/api/chat',
            '/api/conversation/history',
            '/api/conversation/clear',
            '/api/health',
            '/api/status',
            '/api/sessions/new',
            '/api/sessions/list',
            '/api/sessions/{session_id}',
            '/api/sessions/{session_id}/history',
            '/api/sessions/{session_id}/clear'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误，请稍后重试',
        'timestamp': datetime.now().isoformat()
    }), 500

@app.errorhandler(503)
def service_unavailable(error):
    return jsonify({
        'success': False,
        'error': '服务暂时不可用，请稍后重试',
        'timestamp': datetime.now().isoformat()
    }), 503

if __name__ == '__main__':
    print("🚀 启动Amazon购物助手服务 (Qwen3原生版本 - 同步实现)...")
    print("🛒 支持Amazon商品搜索、购买和智能对话")
    print("🧠 基于Qwen3-32B模型的原生API调用")
    print("🔧 支持qwen-agent MCP工具调用")
    print("🤔 多思考模式支持（启用/禁用/自动）")
    print("📱 完整的多轮对话历史管理")
    print("📱 多用户多会话管理")
    print("⚡ 同步实现，完全解决Flask异步问题")
    print("🎭 模拟MCP工具响应，优雅降级处理")
    print("🌐 访问地址: http://localhost:5000")
    print()
    print("🔧 核心API端点:")
    print("   POST /api/chat - Amazon购物对话 (支持user_id和session_id)")
    print("   GET  /api/conversation/history - 获取对话历史")
    print("   POST /api/conversation/clear - 清除对话历史")
    print("   GET  /api/health - 健康检查")
    print("   GET  /api/status - 详细状态")
    print("   GET  / - 服务信息")
    print()
    print("🔧 会话管理端点:")
    print("   POST /api/sessions/new - 创建新会话")
    print("   GET  /api/sessions/list - 获取会话列表")
    print("   DELETE /api/sessions/{session_id} - 删除会话")
    print("   GET  /api/sessions/{session_id}/history - 获取会话历史")
    print("   POST /api/sessions/{session_id}/clear - 清除会话历史")
    print()
    print("💡 使用示例:")
    print("   curl -X POST http://localhost:5000/api/chat \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"message\":\"我想买iPhone\",\"user_id\":\"user123\",\"session_id\":\"session456\"}'")
    print()
    print("🎯 主要改进:")
    print("   ✅ 彻底移除CAMEL框架依赖")
    print("   ✅ 使用Qwen3原生API调用")
    print("   ✅ 支持qwen-agent MCP工具")
    print("   ✅ 修复所有异步调用问题")
    print("   ✅ 完整的多轮对话历史管理")
    print("   ✅ 优雅的降级处理机制")
    print("   ✅ 保留所有原有业务逻辑和提示词")
    
    logger.info("🚀 Amazon购物助手服务启动 (Qwen3原生版本)")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=False
    ) 