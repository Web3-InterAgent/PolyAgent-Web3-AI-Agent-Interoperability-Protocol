#!/usr/bin/env python3
"""
多轮对话管理器
支持会话分类存储，每个对话场景对应一段历史文本
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class ShoppingState(Enum):
    """购物状态枚举"""
    BROWSING = "browsing"           # 浏览商品
    SELECTED = "selected"           # 已选择商品
    COLLECTING_INFO = "collecting_info"  # 收集用户信息
    ORDERING = "ordering"           # 创建订单
    PAYING = "paying"              # 支付处理
    COMPLETED = "completed"        # 完成购买
    TRACKING = "tracking"          # 订单追踪

@dataclass
class UserInfo:
    """用户信息数据结构"""
    full_name: str = ""
    email: str = ""
    shipping_address: Dict[str, str] = None
    
    def __post_init__(self):
        if self.shipping_address is None:
            self.shipping_address = {
                "full_name": "",
                "address": "",
                "city": "",
                "state": "",
                "country": "",
                "postal_code": ""
            }
    
    def is_complete(self) -> bool:
        """检查用户信息是否完整"""
        return (
            bool(self.full_name and self.email) and
            all(self.shipping_address.values())
        )

@dataclass
class ProductInfo:
    """商品信息数据结构"""
    asin: str = ""
    title: str = ""
    url: str = ""
    price: str = ""
    rating: str = ""
    reviews_count: str = ""
    image_url: str = ""
    description: str = ""
    availability: str = ""
    
    def to_display_dict(self) -> Dict[str, Any]:
        """转换为显示格式"""
        return {
            "商品标题": self.title,
            "价格": self.price,
            "评分": self.rating,
            "评论数": self.reviews_count,
            "可用性": self.availability,
            "商品链接": self.url
        }

@dataclass
class PaymentInfo:
    """支付信息数据结构"""
    order_id: str = ""
    payment_offers: Dict[str, Any] = None
    payment_status: str = "pending"
    external_id: str = ""
    payment_context_token: str = ""
    
    def __post_init__(self):
        if self.payment_offers is None:
            self.payment_offers = {}

@dataclass
class SessionMetadata:
    """会话元数据"""
    session_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    current_state: ShoppingState
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': self.message_count,
            'current_state': self.current_state.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionMetadata':
        return cls(
            session_id=data['session_id'],
            user_id=data['user_id'],
            title=data['title'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            message_count=data['message_count'],
            current_state=ShoppingState(data['current_state'])
        )

class ConversationMemory:
    """
    简易记忆模式的多轮对话管理
    支持会话分类存储，每个对话场景对应一段历史文本
    """
    
    def __init__(self, user_id: str = "default_user", session_id: str = None):
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.simple_history = []  # 简单历史记录
        self.initialized = False
        
        # 设置存储路径
        self._setup_storage_paths()
        
        # 加载或创建会话
        self._load_or_create_session()
    
    def _setup_storage_paths(self):
        """设置存储路径"""
        current_dir = os.path.dirname(__file__)
        self.memory_base_dir = os.path.join(current_dir, "..", "..", "memory_storage")
        self.history_dir = os.path.join(self.memory_base_dir, "history", self.user_id)
        self.config_dir = os.path.join(self.memory_base_dir, "config")
        
        # 创建目录
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 文件路径
        self.session_file = os.path.join(self.history_dir, f"{self.session_id}.json")
        self.sessions_index_file = os.path.join(self.config_dir, f"sessions_{self.user_id}.json")
    
    def _load_or_create_session(self):
        """加载或创建会话"""
        try:
            if os.path.exists(self.session_file):
                # 加载现有会话
                with open(self.session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.simple_history = data.get('history', [])
                print(f"📚 加载会话 {self.session_id}，包含 {len(self.simple_history)} 条消息")
            else:
                # 创建新会话
                self.simple_history = []
                print(f"🆕 创建新会话 {self.session_id}")
            
            self.initialized = True
            
        except Exception as e:
            print(f"⚠️ 加载会话失败: {e}")
            self.simple_history = []
            self.initialized = True
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史，返回OpenAI格式的消息列表"""
        return self.simple_history.copy()
    
    def add_conversation_turn(self, user_message: str, ai_response: str):
        """添加对话轮次到记忆中"""
        self.simple_history.extend([
            {'role': 'user', 'content': user_message},
            {'role': 'assistant', 'content': ai_response}
        ])
        
        # 立即保存到文件
        self._save_session()
        
        print(f"📝 记录对话轮次到会话 {self.session_id}（当前共{len(self.simple_history)}条消息）")
    
    def _save_session(self):
        """保存会话到文件"""
        try:
            session_data = {
                'session_id': self.session_id,
                'user_id': self.user_id,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'history': self.simple_history
            }
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️ 保存会话失败: {e}")
    
    def clear_history(self):
        """清除当前会话的对话历史"""
        self.simple_history = []
        self._save_session()
        print(f"🧹 会话 {self.session_id} 的对话历史已清除")
    
    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'message_count': len(self.simple_history),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

class SessionManager:
    """会话管理器，管理用户的多个对话会话"""
    
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self._setup_storage_paths()
    
    def _setup_storage_paths(self):
        """设置存储路径"""
        current_dir = os.path.dirname(__file__)
        self.memory_base_dir = os.path.join(current_dir, "..", "..", "memory_storage")
        self.history_dir = os.path.join(self.memory_base_dir, "history", self.user_id)
        self.config_dir = os.path.join(self.memory_base_dir, "config")
        
        # 创建目录
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.sessions_index_file = os.path.join(self.config_dir, f"sessions_{self.user_id}.json")
    
    def create_new_session(self, title: str = None) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        
        if title is None:
            title = f"对话 {datetime.now().strftime('%m-%d %H:%M')}"
        
        # 创建会话元数据
        metadata = SessionMetadata(
            session_id=session_id,
            user_id=self.user_id,
            title=title,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            message_count=0,
            current_state=ShoppingState.BROWSING
        )
        
        # 保存到索引
        self._save_session_metadata(metadata)
        
        print(f"🆕 创建新会话: {session_id} - {title}")
        return session_id
    
    def get_sessions_list(self) -> List[Dict[str, Any]]:
        """获取用户的所有会话列表"""
        try:
            if not os.path.exists(self.sessions_index_file):
                return []
            
            with open(self.sessions_index_file, 'r', encoding='utf-8') as f:
                sessions_data = json.load(f)
            
            # 按更新时间排序（最新的在前）
            sessions = [SessionMetadata.from_dict(data) for data in sessions_data]
            sessions.sort(key=lambda x: x.updated_at, reverse=True)
            
            return [session.to_dict() for session in sessions]
            
        except Exception as e:
            print(f"⚠️ 获取会话列表失败: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """删除指定会话"""
        try:
            # 删除会话文件
            session_file = os.path.join(self.history_dir, f"{session_id}.json")
            if os.path.exists(session_file):
                os.remove(session_file)
            
            # 从索引中删除
            sessions = self.get_sessions_list()
            sessions = [s for s in sessions if s['session_id'] != session_id]
            
            with open(self.sessions_index_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
            
            print(f"🗑️ 删除会话: {session_id}")
            return True
            
        except Exception as e:
            print(f"⚠️ 删除会话失败: {e}")
            return False
    
    def _save_session_metadata(self, metadata: SessionMetadata):
        """保存会话元数据到索引"""
        try:
            sessions = []
            if os.path.exists(self.sessions_index_file):
                with open(self.sessions_index_file, 'r', encoding='utf-8') as f:
                    sessions = json.load(f)
            
            # 更新或添加会话
            session_exists = False
            for i, session in enumerate(sessions):
                if session['session_id'] == metadata.session_id:
                    sessions[i] = metadata.to_dict()
                    session_exists = True
                    break
            
            if not session_exists:
                sessions.append(metadata.to_dict())
            
            with open(self.sessions_index_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️ 保存会话元数据失败: {e}")
    
    def update_session_metadata(self, session_id: str, title: str = None, current_state: ShoppingState = None, message_count: int = None):
        """更新会话元数据"""
        try:
            sessions = self.get_sessions_list()
            
            for session_data in sessions:
                if session_data['session_id'] == session_id:
                    metadata = SessionMetadata.from_dict(session_data)
                    
                    if title is not None:
                        metadata.title = title
                    if current_state is not None:
                        metadata.current_state = current_state
                    if message_count is not None:
                        metadata.message_count = message_count
                    
                    metadata.updated_at = datetime.now()
                    
                    self._save_session_metadata(metadata)
                    break
                    
        except Exception as e:
            print(f"⚠️ 更新会话元数据失败: {e}") 